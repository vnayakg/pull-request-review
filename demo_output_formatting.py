#!/usr/bin/env python3
"""
Demo script for improved output formatting.
This script demonstrates the enhanced readability of review outputs.
"""

from pr_review_agent.output_formatter import format_console, format_markdown, format_fallback_text

def demo_structured_output():
    """Demonstrate structured YAML output formatting."""
    print("🎨 Demo: Structured Review Output")
    print("=" * 50)
    
    # Sample structured review data
    review = {
        'summary': 'This PR adds user authentication functionality with good overall quality but some areas need improvement.',
        'key_issues_to_review': [
            {
                'relevant_file': 'src/auth.py',
                'issue_header': 'Missing input validation',
                'issue_content': 'The login function should validate email format and password strength before processing. Consider adding regex validation for email and minimum password requirements.',
                'start_line': 15,
                'end_line': 25,
                'severity': 'high'
            },
            {
                'relevant_file': 'src/auth.py',
                'issue_header': 'Inconsistent error handling',
                'issue_content': 'Some functions return None on error while others raise exceptions. Standardize error handling approach across the module.',
                'start_line': 45,
                'end_line': 55,
                'severity': 'medium'
            },
            {
                'relevant_file': 'tests/test_auth.py',
                'issue_header': 'Missing test coverage',
                'issue_content': 'Add tests for edge cases like empty credentials, malformed emails, and database connection failures.',
                'start_line': 30,
                'end_line': 40,
                'severity': 'low'
            }
        ],
        'technical_analysis': {
            'code_quality': 'Good overall structure with clear separation of concerns',
            'security_considerations': 'Missing input validation could lead to security vulnerabilities',
            'performance_implications': 'Database queries are efficient, no performance concerns',
            'error_handling': 'Inconsistent error handling patterns need standardization'
        },
        'architectural_consistency': {
            'pattern_alignment': 'Follows established patterns for service layer architecture',
            'codebase_conventions': 'Consistent with existing naming conventions and code style',
            'integration_assessment': 'Integrates well with existing user management system'
        },
        'overall_assessment': {
            'key_findings': 'Functional implementation with security and testing gaps',
            'risk_assessment': 'medium',
            'approval_recommendation': 'request_changes',
            'approval_conditions': 'Address input validation and add missing test coverage'
        },
        'confidence': 'high'
    }
    
    print("\n📋 Console Output:")
    print("-" * 30)
    format_console(review, show_confidence=True)
    
    print("\n📄 Markdown Output:")
    print("-" * 30)
    markdown_output = format_markdown(review)
    print(markdown_output[:500] + "..." if len(markdown_output) > 500 else markdown_output)

def demo_fallback_formatting():
    """Demonstrate fallback formatting for unstructured text."""
    print("\n\n🔄 Demo: Fallback Text Formatting")
    print("=" * 50)
    
    # Sample unstructured text (what LLM might return if YAML parsing fails)
    unstructured_text = """
REVIEW SUMMARY:
This pull request implements user authentication functionality. The code is generally well-structured but has several areas that need attention before approval.

SECURITY CONCERNS:
The main security issue is the lack of input validation in the login function. User inputs are not properly sanitized, which could lead to injection attacks. The password hashing implementation looks correct, but the email validation is insufficient.

CODE QUALITY:
The code follows good practices with clear function names and appropriate comments. However, there's inconsistent error handling - some functions return None while others raise exceptions. This should be standardized.

PERFORMANCE:
No significant performance issues identified. Database queries are properly optimized and the authentication flow is efficient.

TESTING:
The test coverage is inadequate. Missing tests for edge cases like empty credentials, malformed emails, and database connection failures. The existing tests only cover happy path scenarios.

RECOMMENDATIONS:
1. Add comprehensive input validation for email and password fields
2. Standardize error handling approach across all functions
3. Add missing test cases for edge scenarios
4. Consider adding rate limiting for login attempts
5. Add logging for security-related events

OVERALL ASSESSMENT:
The implementation is functional but requires changes before approval. The security and testing gaps need to be addressed. Recommend requesting changes with specific conditions for approval.
"""
    
    print("\n📝 Fallback Formatting for Unstructured Text:")
    print("-" * 50)
    format_fallback_text(unstructured_text)

def demo_mixed_content():
    """Demonstrate handling of mixed content."""
    print("\n\n🎭 Demo: Mixed Content Handling")
    print("=" * 50)
    
    # Text that's partially structured but not valid YAML
    mixed_text = """
This is a code review for the authentication feature.

ISSUES FOUND:
1. Missing input validation in login function
2. Inconsistent error handling patterns
3. Insufficient test coverage

SECURITY:
The authentication implementation has potential vulnerabilities due to lack of input validation. The password hashing is correctly implemented using bcrypt.

RECOMMENDATION:
Request changes to address the security and testing concerns before approval.
"""
    
    print("\n📝 Mixed Content Formatting:")
    print("-" * 40)
    format_fallback_text(mixed_text)

if __name__ == "__main__":
    demo_structured_output()
    demo_fallback_formatting()
    demo_mixed_content()
    
    print("\n🎉 Demo completed!")
    print("\nKey improvements:")
    print("✅ Structured YAML output with clear sections")
    print("✅ Color-coded severity levels")
    print("✅ Emoji indicators for better visual scanning")
    print("✅ Fallback formatting for unstructured text")
    print("✅ Rich console output with panels and styling")
    print("✅ Comprehensive markdown generation") 