import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProcessingAnimation } from '@/components/processing-animation';
import type { ProcessingState } from '@/components/processing-animation';

describe('ProcessingAnimation', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders queued state correctly', () => {
    render(<ProcessingAnimation state="queued" />);

    expect(screen.getByText('Queued')).toBeInTheDocument();
    expect(screen.getByText('Waiting to start...')).toBeInTheDocument();
    expect(screen.getByText('⏳')).toBeInTheDocument();
  });

  it('renders transcribing state correctly', () => {
    render(<ProcessingAnimation state="transcribing" progress={25} />);

    expect(screen.getByText('Transcribing')).toBeInTheDocument();
    expect(screen.getByText('Converting speech to text...')).toBeInTheDocument();
    expect(screen.getByText('🎙️')).toBeInTheDocument();
  });

  it('renders analyzing state correctly', () => {
    render(<ProcessingAnimation state="analyzing" progress={50} />);

    expect(screen.getByText('Analyzing')).toBeInTheDocument();
    expect(screen.getByText('Finding viral moments...')).toBeInTheDocument();
    expect(screen.getByText('🧠')).toBeInTheDocument();
  });

  it('renders rendering state correctly', () => {
    render(<ProcessingAnimation state="rendering" progress={75} />);

    expect(screen.getByText('Rendering')).toBeInTheDocument();
    expect(screen.getByText('Creating clips...')).toBeInTheDocument();
    expect(screen.getByText('🎬')).toBeInTheDocument();
  });

  it('renders complete state correctly', () => {
    render(<ProcessingAnimation state="complete" progress={100} />);

    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('All done!')).toBeInTheDocument();
    expect(screen.getByText('✅')).toBeInTheDocument();
    expect(screen.getByText('Processing complete!')).toBeInTheDocument();
    expect(screen.getByText('Your clips are ready to view')).toBeInTheDocument();
  });

  it('renders error state correctly', () => {
    render(<ProcessingAnimation state="error" />);

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('❌')).toBeInTheDocument();
    expect(screen.getByText('Processing failed')).toBeInTheDocument();
    expect(screen.getByText('Please try again or contact support')).toBeInTheDocument();
  });

  it('displays progress percentage', () => {
    render(<ProcessingAnimation state="transcribing" progress={42} />);

    expect(screen.getByText('42%')).toBeInTheDocument();
  });

  it('displays estimated time when provided', () => {
    render(<ProcessingAnimation state="analyzing" progress={30} estimatedTime={120} />);

    expect(screen.getByText(/2m 0s remaining/)).toBeInTheDocument();
  });

  it('formats estimated time correctly for seconds', () => {
    render(<ProcessingAnimation state="transcribing" progress={90} estimatedTime={45} />);

    expect(screen.getByText(/45s remaining/)).toBeInTheDocument();
  });

  it('does not show progress bar for queued state', () => {
    const { container } = render(<ProcessingAnimation state="queued" />);

    // Progress bar should not be in the document for queued state
    const progressBars = container.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBe(0);
  });

  it('does not show progress bar for error state', () => {
    const { container } = render(<ProcessingAnimation state="error" />);

    const progressBars = container.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBe(0);
  });

  it('shows progress bar for processing states', () => {
    const { container } = render(<ProcessingAnimation state="transcribing" progress={50} />);

    const progressBars = container.querySelectorAll('[role="progressbar"]');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  it('displays task name when provided', () => {
    render(
      <ProcessingAnimation
        state="analyzing"
        progress={60}
        taskName="my-awesome-video.mp4"
      />
    );

    expect(screen.getByText('my-awesome-video.mp4')).toBeInTheDocument();
  });

  it('animates dots for processing states', async () => {
    render(<ProcessingAnimation state="transcribing" progress={25} />);

    // Initially should have "Transcribing" with no dots visible
    const initialBadge = screen.getByText('Transcribing');
    expect(initialBadge).toBeInTheDocument();

    // Advance timers to trigger dot animation
    vi.advanceTimersByTime(500);

    // Should now have dots
    expect(screen.getByText('Transcribing')).toBeInTheDocument();
  });

  it('does not animate dots for non-processing states', () => {
    render(<ProcessingAnimation state="complete" progress={100} />);

    const badge = screen.getByText('Complete');
    expect(badge).toBeInTheDocument();

    // Advance timers
    vi.advanceTimersByTime(2000);

    // Should still just say "Complete" without dots
    expect(screen.getByText('Complete')).toBeInTheDocument();
  });

  it('accepts custom className', () => {
    const { container } = render(
      <ProcessingAnimation state="analyzing" progress={50} className="custom-class" />
    );

    const card = container.querySelector('.custom-class');
    expect(card).toBeInTheDocument();
  });

  it('handles zero progress', () => {
    render(<ProcessingAnimation state="transcribing" progress={0} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('handles 100% progress', () => {
    render(<ProcessingAnimation state="rendering" progress={100} />);

    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('does not show estimated time for complete state', () => {
    render(<ProcessingAnimation state="complete" progress={100} estimatedTime={30} />);

    expect(screen.queryByText(/remaining/)).not.toBeInTheDocument();
  });

  describe('State transitions', () => {
    const states: ProcessingState[] = [
      'queued',
      'transcribing',
      'analyzing',
      'rendering',
      'complete',
    ];

    states.forEach((state) => {
      it(`renders ${state} state without errors`, () => {
        const { container } = render(<ProcessingAnimation state={state} progress={50} />);

        expect(container).toBeInTheDocument();
      });
    });
  });
});
