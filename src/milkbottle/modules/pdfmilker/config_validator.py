"""PDFmilker configuration validation with service health checks."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .config import PDFmilkerConfig

logger = logging.getLogger("pdfmilker.config_validator")


class ValidationResult:
    """Represents the result of a validation check."""

    def __init__(
        self,
        is_valid: bool,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.is_valid = is_valid
        self.message = message
        self.details = details or {}
        self.severity = "error" if not is_valid else "info"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "message": self.message,
            "details": self.details,
            "severity": self.severity,
        }


class ServiceHealthCheck:
    """Base class for service health checks."""

    def __init__(self, name: str, timeout: int = 10):
        self.name = name
        self.timeout = timeout

    def check_health(self, config: PDFmilkerConfig) -> ValidationResult:
        """Check service health."""
        raise NotImplementedError("Subclasses must implement check_health")


class GrobidHealthCheck(ServiceHealthCheck):
    """Health check for Grobid service."""

    def __init__(self):
        super().__init__("Grobid", timeout=15)

    def check_health(self, config: PDFmilkerConfig) -> ValidationResult:
        """Check Grobid service health."""
        try:
            if not config.grobid_url:
                return ValidationResult(
                    False, "Grobid URL not configured", {"service": "grobid"}
                )

            # Test Grobid endpoint
            test_url = f"{config.grobid_url.rstrip('/')}/api/processFulltextDocument"

            response = requests.get(
                test_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                return ValidationResult(
                    True,
                    "Grobid service is healthy",
                    {"service": "grobid", "url": config.grobid_url},
                )
            else:
                return ValidationResult(
                    False,
                    f"Grobid service returned status {response.status_code}",
                    {
                        "service": "grobid",
                        "url": config.grobid_url,
                        "status_code": response.status_code,
                    },
                )

        except requests.exceptions.ConnectionError:
            return ValidationResult(
                False,
                "Cannot connect to Grobid service",
                {
                    "service": "grobid",
                    "url": config.grobid_url,
                    "error": "connection_failed",
                },
            )
        except requests.exceptions.Timeout:
            return ValidationResult(
                False,
                "Grobid service request timed out",
                {"service": "grobid", "url": config.grobid_url, "error": "timeout"},
            )
        except Exception as e:
            return ValidationResult(
                False,
                f"Grobid health check failed: {e}",
                {"service": "grobid", "url": config.grobid_url, "error": str(e)},
            )


class MathpixHealthCheck(ServiceHealthCheck):
    """Health check for Mathpix service."""

    def __init__(self):
        super().__init__("Mathpix", timeout=10)

    def check_health(self, config: PDFmilkerConfig) -> ValidationResult:
        """Check Mathpix service health."""
        try:
            if not config.mathpix_app_id or not config.mathpix_app_key:
                return ValidationResult(
                    False,
                    "Mathpix credentials not configured",
                    {"service": "mathpix", "missing": ["app_id", "app_key"]},
                )

            # Test Mathpix API
            test_url = "https://api.mathpix.com/v3/text"
            headers = {
                "app_id": config.mathpix_app_id,
                "app_key": config.mathpix_app_key,
                "Content-Type": "application/json",
            }

            # Simple test request
            test_data = {"src": "x^2 + y^2 = z^2"}

            response = requests.post(
                test_url, json=test_data, headers=headers, timeout=self.timeout
            )

            if response.status_code in [200, 400]:  # 400 is expected for invalid input
                return ValidationResult(
                    True,
                    "Mathpix service is healthy",
                    {"service": "mathpix", "app_id": config.mathpix_app_id[:8] + "..."},
                )
            elif response.status_code == 401:
                return ValidationResult(
                    False,
                    "Mathpix credentials are invalid",
                    {"service": "mathpix", "error": "invalid_credentials"},
                )
            else:
                return ValidationResult(
                    False,
                    f"Mathpix service returned status {response.status_code}",
                    {"service": "mathpix", "status_code": response.status_code},
                )

        except requests.exceptions.ConnectionError:
            return ValidationResult(
                False,
                "Cannot connect to Mathpix service",
                {"service": "mathpix", "error": "connection_failed"},
            )
        except requests.exceptions.Timeout:
            return ValidationResult(
                False,
                "Mathpix service request timed out",
                {"service": "mathpix", "error": "timeout"},
            )
        except Exception as e:
            return ValidationResult(
                False,
                f"Mathpix health check failed: {e}",
                {"service": "mathpix", "error": str(e)},
            )


class PandocHealthCheck(ServiceHealthCheck):
    """Health check for Pandoc installation."""

    def __init__(self):
        super().__init__("Pandoc", timeout=5)

    def check_health(self, config: PDFmilkerConfig) -> ValidationResult:
        """Check Pandoc installation."""
        try:
            # Check if pandoc is available
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode == 0:
                # Extract version from output
                version_line = result.stdout.split("\n")[0]
                version = version_line.replace("pandoc", "").strip()

                return ValidationResult(
                    True,
                    f"Pandoc is available (version: {version})",
                    {"service": "pandoc", "version": version},
                )
            else:
                return ValidationResult(
                    False,
                    "Pandoc is not available or not working",
                    {"service": "pandoc", "return_code": result.returncode},
                )

        except FileNotFoundError:
            return ValidationResult(
                False,
                "Pandoc is not installed",
                {"service": "pandoc", "error": "not_installed"},
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                False,
                "Pandoc version check timed out",
                {"service": "pandoc", "error": "timeout"},
            )
        except Exception as e:
            return ValidationResult(
                False,
                f"Pandoc health check failed: {e}",
                {"service": "pandoc", "error": str(e)},
            )


class ConfigValidator:
    """Configuration validator with comprehensive checks."""

    def __init__(self):
        self.health_checks = {
            "grobid": GrobidHealthCheck(),
            "mathpix": MathpixHealthCheck(),
            "pandoc": PandocHealthCheck(),
        }
        self.validation_results: List[ValidationResult] = []

    def validate_config(self, config: PDFmilkerConfig) -> Dict[str, Any]:
        """
        Validate configuration comprehensively.

        Args:
            config: PDFMilkerConfig instance to validate

        Returns:
            Dictionary with validation results
        """
        self.validation_results.clear()

        # Basic configuration validation
        basic_results = self._validate_basic_config(config)
        self.validation_results.extend(basic_results)

        # Service health checks
        health_results = self._validate_services(config)
        self.validation_results.extend(health_results)

        # File system validation
        fs_results = self._validate_file_system(config)
        self.validation_results.extend(fs_results)

        # Performance validation
        perf_results = self._validate_performance_settings(config)
        self.validation_results.extend(perf_results)

        return self._generate_validation_summary()

    def _validate_basic_config(self, config: PDFmilkerConfig) -> List[ValidationResult]:
        """Validate basic configuration settings."""
        results = []

        # Check required fields
        if not config.output_dir:
            results.append(
                ValidationResult(
                    False,
                    "Output directory is not configured",
                    {"field": "output_dir", "required": True},
                )
            )

        # Check batch processing settings
        if config.batch_processing.max_workers < 1:
            results.append(
                ValidationResult(
                    False,
                    "Max workers must be at least 1",
                    {
                        "field": "batch_processing.max_workers",
                        "value": config.batch_processing.max_workers,
                    },
                )
            )

        if config.batch_processing.max_workers > 16:
            results.append(
                ValidationResult(
                    False,
                    "Max workers should not exceed 16 for stability",
                    {
                        "field": "batch_processing.max_workers",
                        "value": config.batch_processing.max_workers,
                    },
                )
            )

        # Check memory settings
        if config.memory_management.max_memory_mb < 100:
            results.append(
                ValidationResult(
                    False,
                    "Max memory should be at least 100MB",
                    {
                        "field": "memory_management.max_memory_mb",
                        "value": config.memory_management.max_memory_mb,
                    },
                )
            )

        # Check quality assessment settings
        if not (0.0 <= config.quality_assessment.min_confidence <= 1.0):
            results.append(
                ValidationResult(
                    False,
                    "Min confidence must be between 0.0 and 1.0",
                    {
                        "field": "quality_assessment.min_confidence",
                        "value": config.quality_assessment.min_confidence,
                    },
                )
            )

        return results

    def _validate_services(self, config: PDFmilkerConfig) -> List[ValidationResult]:
        """Validate service configurations and health."""
        results = []

        # Check Grobid
        if config.grobid_url:
            grobid_result = self.health_checks["grobid"].check_health(config)
            results.append(grobid_result)
        else:
            results.append(
                ValidationResult(
                    True,
                    "Grobid service not configured (optional)",
                    {"service": "grobid", "status": "not_configured"},
                )
            )

        # Check Mathpix
        if config.mathpix_app_id and config.mathpix_app_key:
            mathpix_result = self.health_checks["mathpix"].check_health(config)
            results.append(mathpix_result)
        else:
            results.append(
                ValidationResult(
                    True,
                    "Mathpix service not configured (optional)",
                    {"service": "mathpix", "status": "not_configured"},
                )
            )

        # Check Pandoc
        pandoc_result = self.health_checks["pandoc"].check_health(config)
        results.append(pandoc_result)

        return results

    def _validate_file_system(self, config: PDFmilkerConfig) -> List[ValidationResult]:
        """Validate file system settings and permissions."""
        results = []

        # Check output directory
        if config.output_dir:
            output_path = Path(config.output_dir)

            if output_path.exists():
                if not output_path.is_dir():
                    results.append(
                        ValidationResult(
                            False,
                            "Output directory path exists but is not a directory",
                            {"path": str(output_path), "type": "file"},
                        )
                    )
                elif not os.access(output_path, os.W_OK):
                    results.append(
                        ValidationResult(
                            False,
                            "Output directory is not writable",
                            {"path": str(output_path), "permission": "write"},
                        )
                    )
            else:
                # Try to create directory
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                    results.append(
                        ValidationResult(
                            True,
                            "Output directory created successfully",
                            {"path": str(output_path), "action": "created"},
                        )
                    )
                except Exception as e:
                    results.append(
                        ValidationResult(
                            False,
                            f"Cannot create output directory: {e}",
                            {"path": str(output_path), "error": str(e)},
                        )
                    )

        # Check temporary directory
        temp_dir = Path(config.temp_dir) if config.temp_dir else Path("/tmp")
        if temp_dir.exists() and not os.access(temp_dir, os.W_OK):
            results.append(
                ValidationResult(
                    False,
                    "Temporary directory is not writable",
                    {"path": str(temp_dir), "permission": "write"},
                )
            )

        return results

    def _validate_performance_settings(
        self, config: PDFmilkerConfig
    ) -> List[ValidationResult]:
        """Validate performance-related settings."""
        results = []

        # Check batch size limits
        if config.batch_processing.batch_size < 1:
            results.append(
                ValidationResult(
                    False,
                    "Batch size must be at least 1",
                    {
                        "field": "batch_processing.batch_size",
                        "value": config.batch_processing.batch_size,
                    },
                )
            )

        if config.batch_processing.batch_size > 1000:
            results.append(
                ValidationResult(
                    False,
                    "Batch size should not exceed 1000 for stability",
                    {
                        "field": "batch_processing.batch_size",
                        "value": config.batch_processing.batch_size,
                    },
                )
            )

        # Check timeout settings
        if config.progress_tracking.timeout_seconds < 30:
            results.append(
                ValidationResult(
                    False,
                    "Timeout should be at least 30 seconds",
                    {
                        "field": "progress_tracking.timeout_seconds",
                        "value": config.progress_tracking.timeout_seconds,
                    },
                )
            )

        # Check memory settings
        if config.memory_management.chunk_size_mb < 1:
            results.append(
                ValidationResult(
                    False,
                    "Chunk size must be at least 1MB",
                    {
                        "field": "memory_management.chunk_size_mb",
                        "value": config.memory_management.chunk_size_mb,
                    },
                )
            )

        return results

    def _generate_validation_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for r in self.validation_results if r.is_valid)
        failed_checks = total_checks - passed_checks

        # Group results by severity
        errors = [r for r in self.validation_results if not r.is_valid]
        warnings = [
            r for r in self.validation_results if r.is_valid and r.severity == "warning"
        ]
        info = [
            r for r in self.validation_results if r.is_valid and r.severity == "info"
        ]

        summary = {
            "overall_valid": failed_checks == 0,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "success_rate": (
                (passed_checks / total_checks * 100) if total_checks > 0 else 0
            ),
            "errors": [r.to_dict() for r in errors],
            "warnings": [r.to_dict() for r in warnings],
            "info": [r.to_dict() for r in info],
            "recommendations": self._generate_recommendations(),
        }

        return summary

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        for result in self.validation_results:
            if not result.is_valid:
                if "grobid" in result.details.get("service", ""):
                    recommendations.append(
                        "Configure Grobid service for enhanced PDF processing"
                    )

                elif "mathpix" in result.details.get("service", ""):
                    recommendations.append(
                        "Configure Mathpix service for better math extraction"
                    )

                elif "pandoc" in result.details.get("service", ""):
                    recommendations.append(
                        "Install Pandoc for format conversion support"
                    )

                elif "output_dir" in result.details.get("field", ""):
                    recommendations.append("Set a valid output directory path")

                elif "max_workers" in result.details.get("field", ""):
                    recommendations.append(
                        "Adjust max workers to a value between 1 and 16"
                    )

        # Add general recommendations
        if not recommendations:
            recommendations.append("Configuration looks good! All checks passed.")

        return recommendations

    def validate_single_service(
        self, service_name: str, config: PDFmilkerConfig
    ) -> ValidationResult:
        """Validate a single service."""
        if service_name not in self.health_checks:
            return ValidationResult(
                False,
                f"Unknown service: {service_name}",
                {"service": service_name, "error": "unknown_service"},
            )

        return self.health_checks[service_name].check_health(config)

    def get_validation_report(self) -> str:
        """Generate a human-readable validation report."""
        if not self.validation_results:
            return "No validation results available."

        report = "PDFmilker Configuration Validation Report\n"
        report += "=" * 50 + "\n\n"

        summary = self._generate_validation_summary()

        report += f"Overall Status: {'✅ VALID' if summary['overall_valid'] else '❌ INVALID'}\n"
        report += f"Total Checks: {summary['total_checks']}\n"
        report += f"Passed: {summary['passed_checks']}\n"
        report += f"Failed: {summary['failed_checks']}\n"
        report += f"Success Rate: {summary['success_rate']:.1f}%\n\n"

        if summary["errors"]:
            report += "❌ ERRORS:\n"
            for error in summary["errors"]:
                report += f"  • {error['message']}\n"
            report += "\n"

        if summary["warnings"]:
            report += "⚠️  WARNINGS:\n"
            for warning in summary["warnings"]:
                report += f"  • {warning['message']}\n"
            report += "\n"

        if summary["recommendations"]:
            report += "💡 RECOMMENDATIONS:\n"
            for rec in summary["recommendations"]:
                report += f"  • {rec}\n"

        return report


# Global config validator instance
config_validator = ConfigValidator()
