# Backend Test Report

- Total: 40
- Passed: 38
- Failed: 0
- Errors: 0
- Skipped: 2

## Test Cases

- `passed` tests.test_admin.test_admin_endpoints_blocked_for_normal_user
- `passed` tests.test_admin.test_admin_dashboard_stats_and_health
- `passed` tests.test_admin.test_admin_stats_uses_repository_interface_without_private_in_memory_state
- `passed` tests.test_admin.test_admin_user_management
- `passed` tests.test_admin.test_admin_conversion_and_job_management
- `passed` tests.test_auth_error_handling.test_auth_profile_backend_errors_return_cors_json
- `passed` tests.test_cleanup.test_remove_temp_tree_deletes_nested_source_files
- `passed` tests.test_conversion_dependencies.test_supported_markitdown_optional_dependencies_are_installed
- `passed` tests.test_conversion_service.test_convert_file_to_markdown_uses_local_markitdown_for_text_file
- `passed` tests.test_conversions_api.test_dev_token_can_convert_and_read_markdown_without_dependency_override
- `passed` tests.test_conversions_api.test_completed_conversion_returns_download_url
- `passed` tests.test_conversions_api.test_post_conversions_converts_small_text_file_and_cleans_source
- `passed` tests.test_conversions_api.test_get_conversions_returns_only_authenticated_user_items
- `passed` tests.test_conversions_api.test_get_conversion_blocks_cross_user_access
- `passed` tests.test_conversions_api.test_markdown_and_download_url_require_completed_conversion
- `passed` tests.test_conversions_api.test_retry_requires_reupload
- `passed` tests.test_conversions_api.test_delete_conversion_marks_deleted_and_removes_markdown
- `passed` tests.test_cors.test_cors_allows_local_frontend_origin
- `passed` tests.test_cors.test_cors_allows_live_vercel_frontend_origin
- `passed` tests.test_health.test_health_returns_ok
- `passed` tests.test_health.test_openapi_has_product_metadata
- `passed` tests.test_limiter.test_limiter_allows_active_slot_when_available
- `passed` tests.test_limiter.test_limiter_uses_pending_when_active_slots_are_full
- `passed` tests.test_limiter.test_limiter_rejects_when_pending_queue_is_full
- `passed` tests.test_limiter.test_limiter_release_promotes_pending_conversion
- `skipped` tests.test_live_auth_flow.test_live_supabase_user_can_load_profile_and_history Set DOC2LLM_LIVE_AUTH_EMAIL and DOC2LLM_LIVE_AUTH_PASSWORD to run the live Supabase auth journey.
- `skipped` tests.test_live_deployment.test_live_deployment_loads_profile_and_history Set DOC2LLM_LIVE_AUTH_EMAIL and DOC2LLM_LIVE_AUTH_PASSWORD to run the live deployment journey.
- `passed` tests.test_settings.test_get_current_user_profile
- `passed` tests.test_settings.test_get_current_user_profile_uses_supabase_auth_endpoint
- `passed` tests.test_settings.test_update_profile_name
- `passed` tests.test_settings.test_change_password_validations
- `passed` tests.test_settings.test_delete_account_removes_data_and_profile
- `passed` tests.test_startup.test_railway_start_command_uses_python_launcher
- `passed` tests.test_startup.test_startup_launcher_reads_port_from_environment
- `passed` tests.test_startup.test_startup_launcher_falls_back_to_railway_port
- `passed` tests.test_startup.test_railway_requirements_include_runtime_server
- `passed` tests.test_validators.test_validate_upload_metadata_accepts_supported_text_file
- `passed` tests.test_validators.test_validate_upload_metadata_rejects_empty_file
- `passed` tests.test_validators.test_validate_upload_metadata_rejects_unsupported_extension
- `passed` tests.test_validators.test_validate_upload_metadata_rejects_pdf_over_25_mb
