"""
Template Engine - Load and process markdown templates.
"""
from pathlib import Path
from typing import Optional, Dict, Any
import re


class TemplateEngine:
    """Engine for loading and processing templates."""
    
    def __init__(self, templates_dir: str = "./templates"):
        self.templates_dir = Path(templates_dir)
    
    def load_template(self, template_name: str) -> Optional[str]:
        """
        Load a template from file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Template content or None if not found
        """
        template_path = self.templates_dir / template_name
        
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        
        return None
    
    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with context variables.
        
        Args:
            template: Template string
            context: Dictionary of variables to substitute
            
        Returns:
            Rendered template
        """
        result = template
        
        # Simple variable substitution: {{ variable }}
        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def get_test_plan_template(self) -> str:
        """Get the test plan template."""
        template = self.load_template("test_plan_generation.md")
        if template:
            return template
        return self._default_test_plan_template()
    
    def get_test_case_template(self) -> str:
        """Get the test case template."""
        template = self.load_template("test_case_generation.md")
        if template:
            return template
        return self._default_test_case_template()
    
    def _default_test_plan_template(self) -> str:
        """Default test plan template."""
        return """# Test Plan: {{ project_name }}

## 1. Introduction
### 1.1 Purpose
{{ purpose }}

### 1.2 Scope
{{ scope }}

## 2. Test Objectives
{{ objectives }}

## 3. Test Approach
### 3.1 Test Levels
- Unit Testing
- Integration Testing
- System Testing
- E2E Testing

### 3.2 Test Types
- Functional Testing
- Regression Testing
- Performance Testing
- Security Testing

## 4. Test Environment
{{ environment }}

## 5. Entry and Exit Criteria
### Entry Criteria
- Requirements approved
- Test environment ready
- Test data prepared

### Exit Criteria
- All critical bugs fixed
- Test coverage >= 80%
- Stakeholder sign-off

## 6. Risk Assessment
{{ risks }}

## 7. Test Schedule
{{ schedule }}

## 8. Resources
{{ resources }}

## 9. Deliverables
- Test Plan
- Test Cases
- Test Reports
- Bug Reports
"""
    
    def _default_test_case_template(self) -> str:
        """Default test case template."""
        return """# Test Cases: {{ feature_name }}

## Test Case Summary
- Total Test Cases: {{ total_cases }}
- High Priority: {{ high_priority }}
- Medium Priority: {{ medium_priority }}
- Low Priority: {{ low_priority }}

## Functional Test Cases

| Test ID | Description | Preconditions | Steps | Expected Result | Priority |
|---------|-------------|---------------|-------|-----------------|----------|
{{ functional_cases }}

## Negative Test Cases

| Test ID | Invalid Scenario | Input | Expected Error | Priority |
|---------|------------------|-------|----------------|----------|
{{ negative_cases }}

## Boundary Value Cases

| Test ID | Boundary Condition | Input | Expected Result | Priority |
|---------|-------------------|-------|-----------------|----------|
{{ boundary_cases }}
"""


# Global template engine instance
_template_engine: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """Get or create template engine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine
