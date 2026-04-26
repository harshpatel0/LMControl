default_settings = {
  "models": {
    "ollama_server": "localhost:11434",

    "skill_installation": {
      "model_name": "gemma4:e4b",
      "temperature": 0.1,
      "keep_alive": 0
    },

    "planner": {
      "model_name": "gemma4:e4b",
      "thinking": True,
      "temperature": 0.7,
      "keep_alive": 0
    },

    "actor": {
      "model_name": "gemma4:e4b",
      "thinking": True,
      "temperature": 0.3,
      "keep_alive": 30,
      "attach_screenshot_of_active_window": False
    },

    "autonomy_actor": {
      "model_name": "gemma4:e4b",
      "thinking": True,
      "temperature": 0.5,
      "keep_alive": 150,
      "attach_screenshot_of_active_window": False
    }
  },
  "orchestrator": {
    "action_settle_time": 4,
    "use_experimental_autonomy_mode": False,

    "planner_architecture": {
      "max_iterations_per_step": 10,
      "max_autonomy_steps": 10,
      "max_replan_loop": 7
    },

    "autonomy_orchestrator": {
      "enforce_max_total_iterations": True,
      "max_total_iterations": 50
    }
  },
  "context_provider": {
    "waiting_period": 4,
    "skip_after_ticks": 10
  }
}