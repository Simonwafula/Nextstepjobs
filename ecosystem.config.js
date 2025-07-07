module.exports = {
  apps: [
    {
      name: 'nextstep-api',
      script: 'uvicorn',
      args: 'server:app --host 0.0.0.0 --port 8001 --workers 4',
      cwd: './backend',
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: './backend'
      },
      error_file: './logs/nextstep-api-error.log',
      out_file: './logs/nextstep-api-out.log',
      log_file: './logs/nextstep-api-combined.log',
      time: true,
      restart_delay: 4000,
      max_restarts: 10,
      min_uptime: '10s'
    }
  ],

  deploy: {
    production: {
      user: 'deploy',
      host: ['your-server-ip'],
      ref: 'origin/main',
      repo: 'https://github.com/Simonwafula/Nextstepjobs.git',
      path: '/var/www/nextstep',
      'pre-deploy-local': '',
      'post-deploy': 'cd backend && pip install -r requirements.txt && cd ../frontend && yarn install && yarn build && pm2 reload ecosystem.config.js --env production',
      'pre-setup': 'mkdir -p /var/www/nextstep/logs'
    }
  }
}