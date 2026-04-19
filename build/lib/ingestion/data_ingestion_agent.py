from typing import Dict, Any, List, Optional
import json
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path
from backend.agents.base import BaseAgent


class DataIngestionAgent(BaseAgent):
    """Agent for ingesting nutrition and market data from various sources"""
    
    def __init__(self):
        super().__init__("Data Ingestion Agent")
        self.supported_formats = ["json", "csv", "xml", "api"]
        self.data_schemas = self._load_data_schemas()
    
    def get_system_prompt(self) -> str:
        return """You are a data ingestion specialist for nutrition and market data.
        Your role is to:
        1. Process and validate incoming nutrition and market data
        2. Transform data into standardized formats
        3. Ensure data quality and consistency
        4. Handle various data sources and formats
        5. Monitor and report on ingestion status
        
        Always maintain data integrity and follow data governance standards.
        Provide clear feedback on data quality issues and suggest improvements."""
    
    def _load_data_schemas(self) -> Dict[str, Dict]:
        """Load data schemas for validation"""
        return {
            "nutrition_data": {
                "required_fields": ["food_name", "calories", "protein", "carbs", "fat"],
                "optional_fields": ["fiber", "sugar", "sodium", "serving_size", "category"],
                "data_types": {
                    "calories": "float",
                    "protein": "float",
                    "carbs": "float",
                    "fat": "float"
                }
            },
            "market_data": {
                "required_fields": ["food_item", "price", "unit"],
                "optional_fields": ["location", "source", "availability", "quality", "seasonal"],
                "data_types": {
                    "price": "float",
                    "unit": "string"
                }
            },
            "user_profile": {
                "required_fields": ["age", "weight", "height", "gender", "activity_level", "goal"],
                "optional_fields": ["dietary_restrictions", "allergies", "preferences"],
                "data_types": {
                    "age": "int",
                    "weight": "float",
                    "height": "float"
                }
            }
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data ingestion requests"""
        action = input_data.get("action", "ingest")
        
        if action == "ingest":
            return await self.ingest_data(input_data)
        elif action == "validate":
            return await self.validate_data(input_data)
        elif action == "transform":
            return await self.transform_data(input_data)
        elif action == "batch_ingest":
            return await self.batch_ingest(input_data)
        elif action == "schedule_ingestion":
            return await self.schedule_ingestion(input_data)
        elif action == "monitor_quality":
            return await self.monitor_data_quality(input_data)
        else:
            return {"error": f"Unknown action: {action}"}
    
    async def ingest_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest data from a single source"""
        try:
            data_source = input_data.get("data_source", "manual")
            data_format = input_data.get("data_format", "json")
            data_type = input_data.get("data_type", "nutrition_data")
            raw_data = input_data.get("data", {})
            
            # Validate data format
            format_validation = await self._validate_format(raw_data, data_format)
            if not format_validation["valid"]:
                return {
                    "error": "Invalid data format",
                    "details": format_validation["errors"]
                }
            
            # Transform data to standard format
            transformed_data = await self._transform_to_standard(raw_data, data_format, data_type)
            
            # Validate against schema
            schema_validation = await self._validate_schema(transformed_data, data_type)
            if not schema_validation["valid"]:
                return {
                    "error": "Schema validation failed",
                    "details": schema_validation["errors"]
                }
            
            # Clean and normalize data
            cleaned_data = await self._clean_and_normalize(transformed_data, data_type)
            
            # Store data
            storage_result = await self._store_data(cleaned_data, data_type, data_source)
            
            # Update indexes
            index_result = await self._update_indexes(cleaned_data, data_type)
            
            return {
                "success": True,
                "data_source": data_source,
                "data_type": data_type,
                "records_processed": len(cleaned_data) if isinstance(cleaned_data, list) else 1,
                "storage_result": storage_result,
                "index_result": index_result,
                "ingestion_timestamp": datetime.now().isoformat(),
                "quality_score": await self._calculate_quality_score(cleaned_data)
            }
            
        except Exception as e:
            return {"error": f"Error ingesting data: {str(e)}"}
    
    async def validate_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data without ingesting"""
        try:
            data = input_data.get("data", {})
            data_type = input_data.get("data_type", "nutrition_data")
            validation_level = input_data.get("validation_level", "full")
            
            validation_results = {
                "format_valid": True,
                "schema_valid": True,
                "quality_issues": [],
                "recommendations": []
            }
            
            # Format validation
            if validation_level in ["format", "full"]:
                format_validation = await self._validate_format(data, "json")
                validation_results["format_valid"] = format_validation["valid"]
                if not format_validation["valid"]:
                    validation_results["quality_issues"].extend(format_validation["errors"])
            
            # Schema validation
            if validation_level in ["schema", "full"]:
                schema_validation = await self._validate_schema(data, data_type)
                validation_results["schema_valid"] = schema_validation["valid"]
                if not schema_validation["valid"]:
                    validation_results["quality_issues"].extend(schema_validation["errors"])
            
            # Quality assessment
            if validation_level == "full":
                quality_assessment = await self._assess_data_quality(data, data_type)
                validation_results["quality_score"] = quality_assessment["score"]
                validation_results["quality_issues"].extend(quality_assessment["issues"])
                validation_results["recommendations"] = quality_assessment["recommendations"]
            
            return {
                "success": True,
                "data_type": data_type,
                "validation_results": validation_results,
                "validation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error validating data: {str(e)}"}
    
    async def transform_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data between formats"""
        try:
            source_format = input_data.get("source_format", "json")
            target_format = input_data.get("target_format", "json")
            data = input_data.get("data", {})
            transformation_rules = input_data.get("transformation_rules", {})
            
            # Transform data
            transformed_data = await self._apply_transformation(
                data, source_format, target_format, transformation_rules
            )
            
            return {
                "success": True,
                "source_format": source_format,
                "target_format": target_format,
                "transformed_data": transformed_data,
                "transformation_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error transforming data: {str(e)}"}
    
    async def batch_ingest(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest multiple data sources"""
        try:
            batch_sources = input_data.get("batch_sources", [])
            batch_size = input_data.get("batch_size", 10)
            
            ingestion_results = []
            total_processed = 0
            total_errors = 0
            
            for source in batch_sources:
                # Ingest each source
                result = await self.ingest_data(source)
                ingestion_results.append(result)
                
                if result.get("success"):
                    total_processed += result.get("records_processed", 0)
                else:
                    total_errors += 1
            
            # Generate batch summary
            batch_summary = await self._generate_batch_summary(ingestion_results)
            
            return {
                "success": True,
                "batch_size": len(batch_sources),
                "total_processed": total_processed,
                "total_errors": total_errors,
                "ingestion_results": ingestion_results,
                "batch_summary": batch_summary,
                "batch_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error in batch ingestion: {str(e)}"}
    
    async def schedule_ingestion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule recurring data ingestion"""
        try:
            schedule_config = input_data.get("schedule_config", {})
            data_source = input_data.get("data_source", {})
            
            # Validate schedule configuration
            schedule_validation = await self._validate_schedule_config(schedule_config)
            if not schedule_validation["valid"]:
                return {
                    "error": "Invalid schedule configuration",
                    "details": schedule_validation["errors"]
                }
            
            # Create schedule
            schedule_id = await self._create_schedule(schedule_config, data_source)
            
            return {
                "success": True,
                "schedule_id": schedule_id,
                "schedule_config": schedule_config,
                "data_source": data_source,
                "next_run": schedule_config.get("next_run"),
                "schedule_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error scheduling ingestion: {str(e)}"}
    
    async def monitor_data_quality(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor data quality metrics"""
        try:
            monitoring_period = input_data.get("monitoring_period", "24h")
            data_type = input_data.get("data_type", "all")
            
            # Get quality metrics
            quality_metrics = await self._calculate_quality_metrics(monitoring_period, data_type)
            
            # Identify issues
            quality_issues = await self._identify_quality_issues(quality_metrics)
            
            # Generate recommendations
            recommendations = await self._generate_quality_recommendations(quality_issues)
            
            return {
                "success": True,
                "monitoring_period": monitoring_period,
                "data_type": data_type,
                "quality_metrics": quality_metrics,
                "quality_issues": quality_issues,
                "recommendations": recommendations,
                "monitoring_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Error monitoring data quality: {str(e)}"}
    
    async def _validate_format(self, data: Any, format_type: str) -> Dict[str, Any]:
        """Validate data format"""
        validation_result = {"valid": True, "errors": []}
        
        if format_type == "json":
            try:
                if isinstance(data, str):
                    json.loads(data)
                elif not isinstance(data, (dict, list)):
                    validation_result["valid"] = False
                    validation_result["errors"].append("Data must be JSON object or array")
            except json.JSONDecodeError as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Invalid JSON: {str(e)}")
        
        elif format_type == "csv":
            if isinstance(data, str):
                try:
                    csv.reader(data.splitlines())
                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Invalid CSV: {str(e)}")
            else:
                validation_result["valid"] = False
                validation_result["errors"].append("CSV data must be string")
        
        return validation_result
    
    async def _validate_schema(self, data: Any, data_type: str) -> Dict[str, Any]:
        """Validate data against schema"""
        validation_result = {"valid": True, "errors": []}
        
        if data_type not in self.data_schemas:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unknown data type: {data_type}")
            return validation_result
        
        schema = self.data_schemas[data_type]
        
        # Handle both single records and arrays
        records = data if isinstance(data, list) else [data]
        
        for i, record in enumerate(records):
            if not isinstance(record, dict):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Record {i} must be an object")
                continue
            
            # Check required fields
            for field in schema["required_fields"]:
                if field not in record:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Record {i} missing required field: {field}")
            
            # Check data types
            for field, expected_type in schema.get("data_types", {}).items():
                if field in record:
                    if not await self._check_data_type(record[field], expected_type):
                        validation_result["valid"] = False
                        validation_result["errors"].append(
                            f"Record {i} field {field} should be {expected_type}"
                        )
        
        return validation_result
    
    async def _transform_to_standard(self, data: Any, source_format: str, data_type: str) -> Any:
        """Transform data to standard format"""
        if source_format == "json":
            return data
        elif source_format == "csv":
            # Convert CSV to JSON
            if isinstance(data, str):
                reader = csv.DictReader(data.splitlines())
                return list(reader)
        elif source_format == "xml":
            # Convert XML to JSON (simplified)
            return {"xml_data": str(data)}
        
        return data
    
    async def _clean_and_normalize(self, data: Any, data_type: str) -> Any:
        """Clean and normalize data"""
        if isinstance(data, list):
            cleaned_records = []
            for record in data:
                cleaned_record = await self._clean_record(record, data_type)
                cleaned_records.append(cleaned_record)
            return cleaned_records
        else:
            return await self._clean_record(data, data_type)
    
    async def _clean_record(self, record: Dict, data_type: str) -> Dict:
        """Clean individual record"""
        cleaned = record.copy()
        
        # Remove null values
        cleaned = {k: v for k, v in cleaned.items() if v is not None}
        
        # Normalize numeric fields
        if data_type == "nutrition_data":
            for field in ["calories", "protein", "carbs", "fat", "fiber", "sugar", "sodium"]:
                if field in cleaned:
                    try:
                        cleaned[field] = float(cleaned[field])
                    except (ValueError, TypeError):
                        cleaned[field] = 0.0
        
        elif data_type == "market_data":
            if "price" in cleaned:
                try:
                    cleaned["price"] = float(cleaned["price"])
                except (ValueError, TypeError):
                    cleaned["price"] = 0.0
        
        # Normalize string fields
        for field, value in cleaned.items():
            if isinstance(value, str):
                cleaned[field] = value.strip().lower()
        
        return cleaned
    
    async def _store_data(self, data: Any, data_type: str, source: str) -> Dict[str, Any]:
        """Store data in appropriate storage"""
        # This would integrate with actual database storage
        return {
            "status": "stored",
            "data_type": data_type,
            "source": source,
            "records": len(data) if isinstance(data, list) else 1,
            "storage_location": f"{data_type}_collection",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _update_indexes(self, data: Any, data_type: str) -> Dict[str, Any]:
        """Update search indexes"""
        # This would update search indexes
        return {
            "status": "updated",
            "indexes": [f"{data_type}_search", f"{data_type}_metadata"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _calculate_quality_score(self, data: Any) -> float:
        """Calculate data quality score"""
        if not data:
            return 0.0
        
        score = 100.0
        
        # Check for completeness
        if isinstance(data, list):
            total_fields = 0
            missing_fields = 0
            for record in data:
                if isinstance(record, dict):
                    total_fields += len(record)
                    missing_fields += sum(1 for v in record.values() if v is None or v == "")
            
            if total_fields > 0:
                completeness = (total_fields - missing_fields) / total_fields
                score *= completeness
        
        return round(score, 1)
    
    async def _assess_data_quality(self, data: Any, data_type: str) -> Dict[str, Any]:
        """Assess overall data quality"""
        issues = []
        recommendations = []
        
        if isinstance(data, list):
            # Check for duplicates
            if len(data) != len(set(json.dumps(d, sort_keys=True) for d in data)):
                issues.append("Duplicate records found")
                recommendations.append("Remove duplicate records")
            
            # Check for empty records
            empty_count = sum(1 for record in data if not record)
            if empty_count > 0:
                issues.append(f"Found {empty_count} empty records")
                recommendations.append("Remove empty records")
        
        score = 100.0 - (len(issues) * 10)
        score = max(0.0, score)
        
        return {
            "score": round(score, 1),
            "issues": issues,
            "recommendations": recommendations
        }
    
    async def _check_data_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_mapping = {
            "string": str,
            "int": int,
            "float": (int, float),
            "bool": bool
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    async def _apply_transformation(self, data: Any, source_format: str, target_format: str, rules: Dict) -> Any:
        """Apply transformation rules"""
        # Simple transformation - in real implementation would be more sophisticated
        if source_format == target_format:
            return data
        
        # Apply field mappings
        if "field_mappings" in rules:
            if isinstance(data, list):
                transformed = []
                for record in data:
                    new_record = {}
                    for target_field, source_field in rules["field_mappings"].items():
                        if source_field in record:
                            new_record[target_field] = record[source_field]
                    transformed.append(new_record)
                return transformed
            elif isinstance(data, dict):
                new_record = {}
                for target_field, source_field in rules["field_mappings"].items():
                    if source_field in data:
                        new_record[target_field] = data[source_field]
                return new_record
        
        return data
    
    async def _generate_batch_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate batch ingestion summary"""
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful
        total_records = sum(r.get("records_processed", 0) for r in results if r.get("success"))
        
        return {
            "total_sources": len(results),
            "successful": successful,
            "failed": failed,
            "success_rate": round((successful / len(results)) * 100, 1) if results else 0,
            "total_records": total_records
        }
    
    async def _validate_schedule_config(self, config: Dict) -> Dict[str, Any]:
        """Validate schedule configuration"""
        validation = {"valid": True, "errors": []}
        
        required_fields = ["frequency", "data_source"]
        for field in required_fields:
            if field not in config:
                validation["valid"] = False
                validation["errors"].append(f"Missing required field: {field}")
        
        return validation
    
    async def _create_schedule(self, config: Dict, data_source: Dict) -> str:
        """Create ingestion schedule"""
        # This would create an actual schedule
        schedule_id = f"schedule_{datetime.now().timestamp()}"
        return schedule_id
    
    async def _calculate_quality_metrics(self, period: str, data_type: str) -> Dict[str, Any]:
        """Calculate quality metrics for monitoring"""
        # Mock metrics
        return {
            "completeness": 95.2,
            "accuracy": 98.1,
            "consistency": 92.7,
            "timeliness": 88.4,
            "total_records": 15420
        }
    
    async def _identify_quality_issues(self, metrics: Dict) -> List[str]:
        """Identify quality issues from metrics"""
        issues = []
        
        if metrics.get("completeness", 100) < 90:
            issues.append("Low data completeness detected")
        
        if metrics.get("accuracy", 100) < 95:
            issues.append("Data accuracy below threshold")
        
        if metrics.get("timeliness", 100) < 85:
            issues.append("Data timeliness needs improvement")
        
        return issues
    
    async def _generate_quality_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations for quality improvement"""
        recommendations = []
        
        for issue in issues:
            if "completeness" in issue:
                recommendations.append("Implement data validation at source")
            elif "accuracy" in issue:
                recommendations.append("Add data verification steps")
            elif "timeliness" in issue:
                recommendations.append("Optimize data pipeline performance")
        
        return recommendations
