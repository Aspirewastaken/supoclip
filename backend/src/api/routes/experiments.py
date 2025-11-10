"""
Experiments API routes for A/B testing clip variations.

Endpoints:
- POST /experiments/create - Create a new A/B test experiment
- GET /experiments/{id} - Get experiment details
- GET /experiments/{id}/results - Get experiment analysis and statistical results
- POST /experiments/{id}/declare-winner - Manually declare a winner
- POST /experiments/{id}/update-metrics - Update metrics for a variation
- GET /experiments/ - List all experiments for a user
- POST /experiments/{id}/pause - Pause an experiment
- POST /experiments/{id}/resume - Resume a paused experiment
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

from ...database import get_db, AsyncSessionLocal
from ...models import Experiment, ExperimentResult, GeneratedClip, User
from ...experiments.ab_testing import (
    ABTestingEngine,
    VariationMetrics,
    ExperimentAnalysis,
    format_experiment_report
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post(
    "/create",
    summary="Create A/B Test Experiment",
    description="""
    Create a new A/B testing experiment to compare clip variations.

    **Variations**: Each variation should include:
    - clip_id: ID of the generated clip to test
    - variation_name: Descriptive name (e.g., "Version A", "Bold Font", "Fast Cuts")

    **Confidence Threshold**: Minimum confidence level (0-1) required to automatically
    declare a winner. Default is 0.95 (95% confidence).

    Example request:
    ```json
    {
        "name": "Font Style Test",
        "description": "Testing TikTok Sans vs Arial Bold",
        "variations": [
            {"clip_id": "clip-uuid-1", "variation_name": "TikTok Sans"},
            {"clip_id": "clip-uuid-2", "variation_name": "Arial Bold"}
        ],
        "confidence_threshold": 0.95
    }
    ```
    """,
    responses={
        201: {
            "description": "Experiment created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "experiment_id": "exp-uuid-123",
                        "message": "Experiment created successfully",
                        "variations": [
                            {"variation_id": "var-1", "clip_id": "clip-uuid-1", "variation_name": "TikTok Sans"},
                            {"variation_id": "var-2", "clip_id": "clip-uuid-2", "variation_name": "Arial Bold"}
                        ]
                    }
                }
            }
        }
    }
)
async def create_experiment(request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new A/B testing experiment"""
    headers = request.headers
    user_id = headers.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        data = await request.json()
        name = data.get("name")
        description = data.get("description", "")
        variations = data.get("variations", [])
        confidence_threshold = data.get("confidence_threshold", 0.95)

        # Validation
        if not name:
            raise HTTPException(status_code=400, detail="Experiment name is required")

        if len(variations) < 2:
            raise HTTPException(status_code=400, detail="At least 2 variations are required")

        # Verify user exists
        user_check = await db.execute(
            text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        if not user_check.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        # Verify all clips exist and belong to the user
        clip_ids = [v["clip_id"] for v in variations]
        clips_check = await db.execute(
            text("""
                SELECT gc.id, t.user_id
                FROM generated_clips gc
                JOIN tasks t ON gc.task_id = t.id
                WHERE gc.id = ANY(:clip_ids)
            """),
            {"clip_ids": clip_ids}
        )
        clips = clips_check.fetchall()

        if len(clips) != len(clip_ids):
            raise HTTPException(status_code=404, detail="One or more clips not found")

        # Verify ownership
        for clip in clips:
            if clip.user_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to use these clips")

        # Create experiment
        experiment_id = await db.execute(
            text("""
                INSERT INTO experiments (user_id, name, description, variations, status, confidence_threshold, started_at)
                VALUES (:user_id, :name, :description, :variations, 'running', :confidence_threshold, NOW())
                RETURNING id
            """),
            {
                "user_id": user_id,
                "name": name,
                "description": description,
                "variations": json.dumps(variations),
                "confidence_threshold": confidence_threshold
            }
        )
        exp_id = experiment_id.fetchone()[0]

        # Create experiment_results entries for each variation
        for variation in variations:
            await db.execute(
                text("""
                    INSERT INTO experiment_results (experiment_id, variation_id, clip_id)
                    VALUES (:experiment_id, :variation_id, :clip_id)
                """),
                {
                    "experiment_id": exp_id,
                    "variation_id": variation["clip_id"],
                    "clip_id": variation["clip_id"]
                }
            )

        await db.commit()

        logger.info(f"Created experiment {exp_id} for user {user_id}")

        return {
            "experiment_id": exp_id,
            "message": "Experiment created successfully",
            "variations": variations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating experiment: {str(e)}")


@router.get("/")
async def list_experiments(request: Request, db: AsyncSession = Depends(get_db)):
    """List all experiments for the authenticated user"""
    headers = request.headers
    user_id = headers.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        result = await db.execute(
            text("""
                SELECT id, name, description, status, winner_variation_id,
                       confidence_threshold, started_at, completed_at, created_at
                FROM experiments
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": user_id}
        )
        experiments = result.fetchall()

        experiments_list = []
        for exp in experiments:
            experiments_list.append({
                "id": exp.id,
                "name": exp.name,
                "description": exp.description,
                "status": exp.status,
                "winner_variation_id": exp.winner_variation_id,
                "confidence_threshold": exp.confidence_threshold,
                "started_at": exp.started_at.isoformat() if exp.started_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "created_at": exp.created_at.isoformat() if exp.created_at else None
            })

        return {
            "experiments": experiments_list,
            "total": len(experiments_list)
        }

    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing experiments: {str(e)}")


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Get experiment details"""
    try:
        result = await db.execute(
            text("""
                SELECT e.*,
                       (SELECT json_agg(json_build_object(
                           'id', er.id,
                           'variation_id', er.variation_id,
                           'clip_id', er.clip_id,
                           'views', er.views,
                           'clicks', er.clicks,
                           'conversions', er.conversions,
                           'shares', er.shares,
                           'likes', er.likes,
                           'comments', er.comments,
                           'click_through_rate', er.click_through_rate,
                           'conversion_rate', er.conversion_rate,
                           'engagement_rate', er.engagement_rate,
                           'avg_watch_time', er.avg_watch_time,
                           'watch_completion_rate', er.watch_completion_rate
                       )) FROM experiment_results er WHERE er.experiment_id = e.id) as results
                FROM experiments e
                WHERE e.id = :experiment_id
            """),
            {"experiment_id": experiment_id}
        )
        exp = result.fetchone()

        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        return {
            "id": exp.id,
            "user_id": exp.user_id,
            "name": exp.name,
            "description": exp.description,
            "variations": json.loads(exp.variations) if exp.variations else [],
            "status": exp.status,
            "winner_variation_id": exp.winner_variation_id,
            "confidence_threshold": exp.confidence_threshold,
            "started_at": exp.started_at.isoformat() if exp.started_at else None,
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            "results": exp.results if exp.results else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting experiment: {str(e)}")


@router.get(
    "/{experiment_id}/results",
    summary="Get Experiment Analysis",
    description="""
    Get comprehensive statistical analysis of an A/B test experiment.

    Returns:
    - Variation metrics (views, CTR, conversion rate, engagement, etc.)
    - Statistical test results (chi-square, t-test)
    - Bayesian probabilities
    - Overall winner recommendation
    - Confidence levels
    - Sample size adequacy
    """,
)
async def get_experiment_results(experiment_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed statistical analysis of experiment results"""
    try:
        # Get experiment
        exp_result = await db.execute(
            text("SELECT * FROM experiments WHERE id = :experiment_id"),
            {"experiment_id": experiment_id}
        )
        exp = exp_result.fetchone()

        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        # Get results
        results_query = await db.execute(
            text("""
                SELECT * FROM experiment_results
                WHERE experiment_id = :experiment_id
            """),
            {"experiment_id": experiment_id}
        )
        results = results_query.fetchall()

        # Get variation names from experiment variations JSON
        variations_data = json.loads(exp.variations) if exp.variations else []
        variation_name_map = {v["clip_id"]: v["variation_name"] for v in variations_data}

        # Convert to VariationMetrics objects
        variation_metrics = []
        for result in results:
            metrics = VariationMetrics(
                variation_id=result.variation_id,
                variation_name=variation_name_map.get(result.variation_id, f"Variation {result.variation_id[:8]}"),
                views=result.views,
                clicks=result.clicks,
                conversions=result.conversions,
                shares=result.shares,
                likes=result.likes,
                comments=result.comments,
                click_through_rate=result.click_through_rate,
                conversion_rate=result.conversion_rate,
                engagement_rate=result.engagement_rate,
                avg_watch_time=result.avg_watch_time,
                watch_completion_rate=result.watch_completion_rate
            )
            metrics.calculate_rates()
            variation_metrics.append(metrics)

        # Perform statistical analysis
        engine = ABTestingEngine(
            min_sample_size=100,
            significance_level=0.05,
            confidence_threshold=exp.confidence_threshold
        )

        analysis = engine.analyze_experiment(experiment_id, variation_metrics)

        # Check if winner should be automatically declared
        if analysis.should_declare_winner and exp.status == "running":
            # Auto-declare winner
            await db.execute(
                text("""
                    UPDATE experiments
                    SET winner_variation_id = :winner_id,
                        status = 'completed',
                        completed_at = NOW()
                    WHERE id = :experiment_id
                """),
                {
                    "winner_id": analysis.overall_winner,
                    "experiment_id": experiment_id
                }
            )
            await db.commit()
            logger.info(f"Auto-declared winner {analysis.overall_winner} for experiment {experiment_id}")

        # Format response
        return {
            "experiment_id": experiment_id,
            "experiment_name": exp.name,
            "status": exp.status,
            "variations": [
                {
                    "variation_id": vm.variation_id,
                    "variation_name": vm.variation_name,
                    "metrics": {
                        "views": vm.views,
                        "clicks": vm.clicks,
                        "conversions": vm.conversions,
                        "shares": vm.shares,
                        "likes": vm.likes,
                        "comments": vm.comments,
                        "click_through_rate": vm.click_through_rate,
                        "conversion_rate": vm.conversion_rate,
                        "engagement_rate": vm.engagement_rate,
                        "avg_watch_time": vm.avg_watch_time,
                        "watch_completion_rate": vm.watch_completion_rate
                    }
                }
                for vm in analysis.variations
            ],
            "statistical_tests": [test.to_dict() for test in analysis.test_results],
            "overall_winner": analysis.overall_winner,
            "overall_confidence": analysis.overall_confidence,
            "recommendation": analysis.recommendation,
            "should_declare_winner": analysis.should_declare_winner,
            "min_sample_size_reached": analysis.min_sample_size_reached,
            "report": format_experiment_report(analysis)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing experiment: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing experiment: {str(e)}")


@router.post("/{experiment_id}/declare-winner")
async def declare_winner(experiment_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Manually declare a winner for an experiment"""
    headers = request.headers
    user_id = headers.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        data = await request.json()
        winner_variation_id = data.get("winner_variation_id")

        if not winner_variation_id:
            raise HTTPException(status_code=400, detail="Winner variation ID is required")

        # Verify experiment exists and user owns it
        exp_check = await db.execute(
            text("SELECT user_id, status FROM experiments WHERE id = :experiment_id"),
            {"experiment_id": experiment_id}
        )
        exp = exp_check.fetchone()

        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        if exp.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this experiment")

        # Verify winner variation exists
        variation_check = await db.execute(
            text("""
                SELECT 1 FROM experiment_results
                WHERE experiment_id = :experiment_id AND variation_id = :variation_id
            """),
            {"experiment_id": experiment_id, "variation_id": winner_variation_id}
        )

        if not variation_check.fetchone():
            raise HTTPException(status_code=404, detail="Variation not found in this experiment")

        # Update experiment
        await db.execute(
            text("""
                UPDATE experiments
                SET winner_variation_id = :winner_id,
                    status = 'completed',
                    completed_at = NOW()
                WHERE id = :experiment_id
            """),
            {"winner_id": winner_variation_id, "experiment_id": experiment_id}
        )
        await db.commit()

        logger.info(f"Manually declared winner {winner_variation_id} for experiment {experiment_id}")

        return {
            "message": "Winner declared successfully",
            "experiment_id": experiment_id,
            "winner_variation_id": winner_variation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declaring winner: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error declaring winner: {str(e)}")


@router.post("/{experiment_id}/update-metrics")
async def update_variation_metrics(experiment_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Update metrics for a variation (for testing or manual entry)"""
    headers = request.headers
    user_id = headers.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        data = await request.json()
        variation_id = data.get("variation_id")
        metrics = data.get("metrics", {})

        if not variation_id:
            raise HTTPException(status_code=400, detail="Variation ID is required")

        # Verify experiment exists and user owns it
        exp_check = await db.execute(
            text("SELECT user_id FROM experiments WHERE id = :experiment_id"),
            {"experiment_id": experiment_id}
        )
        exp = exp_check.fetchone()

        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        if exp.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this experiment")

        # Build update query dynamically based on provided metrics
        updates = []
        params = {"experiment_id": experiment_id, "variation_id": variation_id}

        for key, value in metrics.items():
            if key in ["views", "clicks", "conversions", "shares", "likes", "comments",
                       "click_through_rate", "conversion_rate", "engagement_rate",
                       "avg_watch_time", "watch_completion_rate"]:
                updates.append(f"{key} = :{key}")
                params[key] = value

        if not updates:
            raise HTTPException(status_code=400, detail="No valid metrics provided")

        # Update metrics
        query = f"""
            UPDATE experiment_results
            SET {', '.join(updates)}
            WHERE experiment_id = :experiment_id AND variation_id = :variation_id
        """

        await db.execute(text(query), params)
        await db.commit()

        logger.info(f"Updated metrics for variation {variation_id} in experiment {experiment_id}")

        return {
            "message": "Metrics updated successfully",
            "experiment_id": experiment_id,
            "variation_id": variation_id,
            "updated_metrics": metrics
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating metrics: {str(e)}")


@router.post("/{experiment_id}/pause")
async def pause_experiment(experiment_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Pause a running experiment"""
    headers = request.headers
    user_id = headers.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        # Verify ownership
        exp_check = await db.execute(
            text("SELECT user_id, status FROM experiments WHERE id = :experiment_id"),
            {"experiment_id": experiment_id}
        )
        exp = exp_check.fetchone()

        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        if exp.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this experiment")

        if exp.status != "running":
            raise HTTPException(status_code=400, detail="Can only pause running experiments")

        # Pause experiment
        await db.execute(
            text("UPDATE experiments SET status = 'paused' WHERE id = :experiment_id"),
            {"experiment_id": experiment_id}
        )
        await db.commit()

        return {"message": "Experiment paused successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing experiment: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error pausing experiment: {str(e)}")


@router.post("/{experiment_id}/resume")
async def resume_experiment(experiment_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Resume a paused experiment"""
    headers = request.headers
    user_id = headers.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        # Verify ownership
        exp_check = await db.execute(
            text("SELECT user_id, status FROM experiments WHERE id = :experiment_id"),
            {"experiment_id": experiment_id}
        )
        exp = exp_check.fetchone()

        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")

        if exp.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this experiment")

        if exp.status != "paused":
            raise HTTPException(status_code=400, detail="Can only resume paused experiments")

        # Resume experiment
        await db.execute(
            text("UPDATE experiments SET status = 'running' WHERE id = :experiment_id"),
            {"experiment_id": experiment_id}
        )
        await db.commit()

        return {"message": "Experiment resumed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming experiment: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resuming experiment: {str(e)}")
