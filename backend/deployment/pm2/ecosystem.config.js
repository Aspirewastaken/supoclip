/**
 * PM2 Ecosystem Configuration for SupoClip Workers
 *
 * Installation:
 *   npm install -g pm2
 *   pm2 start ecosystem.config.js
 *
 * Management:
 *   pm2 status
 *   pm2 logs supoclip-worker
 *   pm2 restart supoclip-worker
 *   pm2 stop supoclip-worker
 *   pm2 delete supoclip-worker
 *
 * Auto-start on boot:
 *   pm2 startup
 *   pm2 save
 */

module.exports = {
  apps: [
    {
      // Application name
      name: 'supoclip-worker',

      // Script to run
      script: '.venv/bin/arq',
      args: 'src.workers.tasks.WorkerSettings',

      // Working directory
      cwd: '/opt/supoclip/backend',

      // Execution mode
      exec_mode: 'fork',  // Use 'fork' for Python processes

      // Number of instances (scale horizontally)
      // Set to 1 for single worker, or higher for multiple workers
      // Use 'max' to auto-scale based on CPU cores
      instances: 2,

      // Auto-restart behavior
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',  // Minimum uptime before restart is considered stable
      restart_delay: 5000,  // Delay between restarts (ms)

      // Resource limits
      max_memory_restart: '4G',  // Restart if memory exceeds 4GB

      // Environment variables
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/opt/supoclip/backend',
        PYTHONUNBUFFERED: '1',
        REDIS_HOST: 'localhost',
        REDIS_PORT: '6379',
      },

      // Environment variables for development
      env_development: {
        NODE_ENV: 'development',
        PYTHONPATH: '/opt/supoclip/backend',
        PYTHONUNBUFFERED: '1',
        REDIS_HOST: 'localhost',
        REDIS_PORT: '6379',
      },

      // Environment variables for staging
      env_staging: {
        NODE_ENV: 'staging',
        PYTHONPATH: '/opt/supoclip/backend',
        PYTHONUNBUFFERED: '1',
        REDIS_HOST: 'redis-staging',
        REDIS_PORT: '6379',
      },

      // Logging
      error_file: '/var/log/supoclip/worker-error.log',
      out_file: '/var/log/supoclip/worker-out.log',
      log_file: '/var/log/supoclip/worker-combined.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,  // Merge logs from all instances

      // Watch for file changes (disable in production)
      watch: false,
      ignore_watch: ['node_modules', 'logs', '*.log'],

      // Source maps
      source_map_support: false,

      // Graceful shutdown
      kill_timeout: 30000,  // 30 seconds for graceful shutdown
      wait_ready: true,
      listen_timeout: 10000,

      // Health check
      // PM2 will restart if health check fails
      health_check: {
        url: 'http://localhost:8000/health',
        interval: 30000,  // Check every 30 seconds
        timeout: 5000,
      },

      // Instance variables
      // Access via process.env.instance_var or process.env.pm_id
      instance_var: 'INSTANCE_ID',

      // Post-deploy actions
      // Uncomment if using PM2 deploy feature
      // post_deploy: 'npm install && pm2 reload ecosystem.config.js --env production',
    },

    // Optional: Separate worker for high-priority tasks
    {
      name: 'supoclip-worker-priority',
      script: '.venv/bin/arq',
      args: 'src.workers.tasks.WorkerSettings',
      cwd: '/opt/supoclip/backend',
      exec_mode: 'fork',
      instances: 1,
      autorestart: true,
      max_memory_restart: '4G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/opt/supoclip/backend',
        PYTHONUNBUFFERED: '1',
        REDIS_HOST: 'localhost',
        REDIS_PORT: '6379',
        WORKER_PRIORITY: 'high',  // Custom env var
      },
      error_file: '/var/log/supoclip/worker-priority-error.log',
      out_file: '/var/log/supoclip/worker-priority-out.log',
    },
  ],

  // Deployment configuration
  // Use: pm2 deploy ecosystem.config.js production setup
  deploy: {
    production: {
      // SSH connection
      user: 'deploy',
      host: ['production-server-1', 'production-server-2'],
      ref: 'origin/main',
      repo: 'git@github.com:your-org/supoclip.git',
      path: '/opt/supoclip',

      // Commands
      'pre-deploy-local': 'echo "Deploying to production..."',
      'post-deploy': 'cd backend && uv sync && pm2 reload ecosystem.config.js --env production',
      'pre-setup': 'apt-get update && apt-get install -y python3.11 redis-server',

      // SSH options
      ssh_options: 'StrictHostKeyChecking=no',
    },

    staging: {
      user: 'deploy',
      host: 'staging-server',
      ref: 'origin/develop',
      repo: 'git@github.com:your-org/supoclip.git',
      path: '/opt/supoclip',
      'post-deploy': 'cd backend && uv sync && pm2 reload ecosystem.config.js --env staging',
    },
  },
};
