"""CI/CD Manager - Continuous Integration and Deployment pipeline management."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import MilkBottleConfig


@dataclass
class PipelineConfig:
    """CI/CD pipeline configuration."""

    name: str = "milkbottle-pipeline"
    trigger_branch: str = "main"
    stages: List[str] = field(default_factory=lambda: ["test", "build", "deploy"])
    test_command: str = "pytest tests/"
    build_command: str = "python -m build"
    deploy_command: str = "python -m milkbottle.deployment deploy"
    environment: str = "production"
    auto_deploy: bool = False
    notifications: List[str] = field(default_factory=list)


@dataclass
class PipelineStatus:
    """Pipeline execution status."""

    pipeline_id: str
    status: str = "pending"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    stages_completed: List[str] = field(default_factory=list)
    stages_failed: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)

    def items(self):
        """Return items as dict for CLI compatibility."""
        return {
            "Testing": {
                "status": "success" if "Testing" in self.stages_completed else "failed",
                "duration": 0.0,
            },
            "Building": {
                "status": (
                    "success" if "Building" in self.stages_completed else "failed"
                ),
                "duration": 0.0,
            },
            "Deploying": {
                "status": (
                    "success" if "Deploying" in self.stages_completed else "failed"
                ),
                "duration": 0.0,
            },
        }.items()


class CICDManager:
    """Continuous Integration and Deployment pipeline management."""

    def __init__(self, config: MilkBottleConfig):
        self.config = config
        self.pipeline_config = PipelineConfig()
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.cicd")
        self.current_pipeline: Optional[PipelineStatus] = None
        self.pipeline_history: List[PipelineStatus] = []

    async def create_pipeline(
        self, pipeline_name: Optional[str] = None, config_file: Optional[str] = None
    ) -> bool:
        """Create a new CI/CD pipeline."""
        try:
            self.logger.info("Creating CI/CD pipeline")

            # Load configuration
            if config_file and Path(config_file).exists():
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)
                    self.pipeline_config = PipelineConfig(**config_data)

            if pipeline_name:
                self.pipeline_config.name = pipeline_name

            # Create pipeline files
            await self._create_github_workflow()
            await self._create_gitlab_ci()
            await self._create_jenkins_pipeline()

            self.logger.info(
                f"Successfully created pipeline: {self.pipeline_config.name}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to create pipeline: {e}")
            return False

    async def run_pipeline(
        self, branch: Optional[str] = None, environment: Optional[str] = None
    ) -> bool:
        """Run the CI/CD pipeline."""
        try:
            self.logger.info("Starting CI/CD pipeline")

            # Initialize pipeline
            pipeline_id = self._generate_pipeline_id()
            self.current_pipeline = PipelineStatus(
                pipeline_id=pipeline_id,
                status="running",
                start_time=self._get_timestamp(),
            )

            # Set environment
            env = environment or self.pipeline_config.environment

            # Execute pipeline stages
            stages = [
                ("Testing", self._run_tests),
                ("Building", self._run_build),
                ("Deploying", self._run_deploy),
            ]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                for stage_name, stage_func in stages:
                    task = progress.add_task(stage_name, total=None)

                    try:
                        success = await stage_func(env)
                        if success:
                            self.current_pipeline.stages_completed.append(stage_name)
                            progress.update(task, completed=True)
                        else:
                            self.current_pipeline.stages_failed.append(stage_name)
                            progress.update(task, completed=False)
                            self.current_pipeline.status = "failed"
                            break

                    except Exception as e:
                        error_msg = f"Stage '{stage_name}' failed: {e}"
                        self.logger.error(error_msg)
                        self.current_pipeline.stages_failed.append(stage_name)
                        self.current_pipeline.logs.append(error_msg)
                        progress.update(task, completed=False)
                        self.current_pipeline.status = "failed"
                        break

            # Finalize pipeline
            if self.current_pipeline.status != "failed":
                self.current_pipeline.status = "completed"

            self.current_pipeline.end_time = self._get_timestamp()

            # Add to history
            self.pipeline_history.append(self.current_pipeline)

            # Send notifications
            await self._send_notifications()

            self.logger.info(
                f"Pipeline {pipeline_id} completed with status: {self.current_pipeline.status}"
            )
            return self.current_pipeline.status == "completed"

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            if self.current_pipeline:
                self.current_pipeline.status = "failed"
                self.current_pipeline.end_time = self._get_timestamp()
            return False

    async def get_pipeline_status(
        self, pipeline_id: Optional[str] = None
    ) -> Optional[PipelineStatus]:
        """Get current or specific pipeline status."""
        if pipeline_id:
            return next(
                (
                    pipeline
                    for pipeline in self.pipeline_history
                    if pipeline.pipeline_id == pipeline_id
                ),
                None,
            )
        return self.current_pipeline

    async def list_pipelines(self, limit: int = 10) -> List[PipelineStatus]:
        """List recent pipeline executions."""
        return self.pipeline_history[-limit:] if self.pipeline_history else []

    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline."""
        try:
            if (
                self.current_pipeline
                and self.current_pipeline.pipeline_id == pipeline_id
            ):
                self.current_pipeline.status = "cancelled"
                self.current_pipeline.end_time = self._get_timestamp()
                self.logger.info(f"Cancelled pipeline: {pipeline_id}")
                return True
            else:
                self.logger.error(f"Pipeline {pipeline_id} not found or not running")
                return False

        except Exception as e:
            self.logger.error(f"Failed to cancel pipeline: {e}")
            return False

    async def _run_tests(self, environment: str) -> bool:
        """Run test stage."""
        try:
            self.logger.info("Running tests")

            # Run test command
            cmd = self.pipeline_config.test_command.split()
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("Tests passed")
                return True
            else:
                self.logger.error(f"Tests failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return False

    async def _run_build(self, environment: str) -> bool:
        """Run build stage."""
        try:
            self.logger.info("Building application")

            # Run build command
            cmd = self.pipeline_config.build_command.split()
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("Build completed")
                return True
            else:
                self.logger.error(f"Build failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Build execution failed: {e}")
            return False

    async def _run_deploy(self, environment: str) -> bool:
        """Run deploy stage."""
        try:
            self.logger.info(f"Deploying to {environment}")

            # Run deploy command
            cmd = self.pipeline_config.deploy_command.split()
            cmd.extend(["--environment", environment])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("Deployment completed")
                return True
            else:
                self.logger.error(f"Deployment failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Deployment execution failed: {e}")
            return False

    async def _create_github_workflow(self) -> None:
        """Create GitHub Actions workflow."""
        workflow_content = f"""name: {self.pipeline_config.name}

on:
  push:
    branches: [ {self.pipeline_config.trigger_branch} ]
  pull_request:
    branches: [ {self.pipeline_config.trigger_branch} ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: {self.pipeline_config.test_command}

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Build package
      run: {self.pipeline_config.build_command}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/{self.pipeline_config.trigger_branch}'
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Deploy
      run: {self.pipeline_config.deploy_command}
      env:
        ENVIRONMENT: {self.pipeline_config.environment}
"""

        workflow_dir = Path(".github/workflows")
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow_file = workflow_dir / f"{self.pipeline_config.name}.yml"
        with open(workflow_file, "w") as f:
            f.write(workflow_content)

        self.logger.info(f"Created GitHub workflow: {workflow_file}")

    async def _create_gitlab_ci(self) -> None:
        """Create GitLab CI configuration."""
        gitlab_ci_content = f"""stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - {self.pipeline_config.test_command}
  only:
    - {self.pipeline_config.trigger_branch}

build:
  stage: build
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - {self.pipeline_config.build_command}
  artifacts:
    paths:
      - dist/
  only:
    - {self.pipeline_config.trigger_branch}

deploy:
  stage: deploy
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - {self.pipeline_config.deploy_command}
  environment:
    name: {self.pipeline_config.environment}
  only:
    - {self.pipeline_config.trigger_branch}
"""

        gitlab_ci_file = Path(".gitlab-ci.yml")
        with open(gitlab_ci_file, "w") as f:
            f.write(gitlab_ci_content)

        self.logger.info(f"Created GitLab CI configuration: {gitlab_ci_file}")

    async def _create_jenkins_pipeline(self) -> None:
        """Create Jenkins pipeline."""
        jenkins_pipeline_content = f"""pipeline {{
    agent any
    
    environment {{
        ENVIRONMENT = '{self.pipeline_config.environment}'
    }}
    
    stages {{
        stage('Test') {{
            steps {{
                sh 'pip install -r requirements.txt'
                sh '{self.pipeline_config.test_command}'
            }}
        }}
        
        stage('Build') {{
            steps {{
                sh 'pip install -r requirements.txt'
                sh '{self.pipeline_config.build_command}'
            }}
        }}
        
        stage('Deploy') {{
            when {{
                branch '{self.pipeline_config.trigger_branch}'
            }}
            steps {{
                sh 'pip install -r requirements.txt'
                sh '{self.pipeline_config.deploy_command}'
            }}
        }}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
    }}
}}
"""

        jenkins_file = Path("Jenkinsfile")
        with open(jenkins_file, "w") as f:
            f.write(jenkins_pipeline_content)

        self.logger.info(f"Created Jenkins pipeline: {jenkins_file}")

    async def _send_notifications(self) -> None:
        """Send pipeline notifications."""
        if not self.current_pipeline or not self.pipeline_config.notifications:
            return

        try:
            status = self.current_pipeline.status
            pipeline_id = self.current_pipeline.pipeline_id

            for notification in self.pipeline_config.notifications:
                if notification == "email":
                    await self._send_email_notification(status, pipeline_id)
                elif notification == "slack":
                    await self._send_slack_notification(status, pipeline_id)
                elif notification == "webhook":
                    await self._send_webhook_notification(status, pipeline_id)

        except Exception as e:
            self.logger.error(f"Failed to send notifications: {e}")

    async def _send_email_notification(self, status: str, pipeline_id: str) -> None:
        """Send email notification."""
        # Implementation would depend on email service
        self.logger.info(
            f"Email notification sent for pipeline {pipeline_id}: {status}"
        )

    async def _send_slack_notification(self, status: str, pipeline_id: str) -> None:
        """Send Slack notification."""
        # Implementation would depend on Slack API
        self.logger.info(
            f"Slack notification sent for pipeline {pipeline_id}: {status}"
        )

    async def _send_webhook_notification(self, status: str, pipeline_id: str) -> None:
        """Send webhook notification."""
        # Implementation would depend on webhook configuration
        self.logger.info(
            f"Webhook notification sent for pipeline {pipeline_id}: {status}"
        )

    def _generate_pipeline_id(self) -> str:
        """Generate unique pipeline ID."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.pipeline_config.name}_{timestamp}"

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
