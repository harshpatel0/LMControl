default_settings = {
    "active_model_provider": "ollama",
    "model_providers": {
        "ollama": {
            "server_url": "localhost:11434",
            "timeout": 120,
        },
        "anthropic": {
            "api_key_env_var": "ANTHROPIC_API_KEY",
            "base_url": None,
            "effort": "medium",
        },
        "google": {
            "api_key_env_var": "GOOGLE_API_KEY",
        },
    },
    "models": {
        "skill_installation": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "temperature": 0.1,
            "keep_alive": 0,
        },
        "planner": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.7,
            "keep_alive": 0,
        },
        "actor": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.3,
            "keep_alive": 30,
            "attach_screenshot_of_active_window": True,
        },
        "autonomy_actor": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.5,
            "keep_alive": 150,
            "attach_screenshot_of_active_window": True,
        },
    },
    "orchestrator": {
        "action_settle_time": 4,
        "use_autonomy_mode": True,
        "planner_architecture": {
            "max_iterations_per_step": 10,
            "max_autonomy_steps": 10,
            "max_replan_loop": 7,
        },
        "autonomy_orchestrator": {
            "max_total_iterations": 50,
        },
    },
    "context_provider": {
        "waiting_period": 4,
        "skip_after_ticks": 10,
        "take_full_screen_screenshot": True,
        "screenshot_quality_percentage": 80,
        "provide_uia_tree": True,
    },
    "skills": {
        "skill_timeout": 0,
    },
}
