# Component Classification & Lifecycle Audit (Phase 1.1 Reconciled)

## 1. Executive Summary & Governance Rules

In accordance with `PLATFORM_GOVERNANCE.md`, every imported component is classified into:
1. Exactly **one primary taxonomy classification**: `CORE`, `PLATFORM`, `ADAPTER`, `EXAMPLE`, `EXPERIMENTAL`, `LEGACY`, `BROKEN`, `DUPLICATE`, `CANDIDATE-FOR-PLATFORM`.
2. Exactly **one lifecycle status**: `EXPERIMENT`, `PROTOTYPE`, `INTERNAL`, `BETA`, `PRODUCTION-CANDIDATE`, `PRODUCTION`, `DEPRECATED`.

---

## 2. Reconciled Classification Metrics (160 Components)

### Primary Taxonomy Classification Totals

| Classification | Count | Percentage | Action Plan |
| :--- | :---: | :---: | :--- |
| `CORE` | 0 | 0.0% | To be built in Phase 2 Platform Kernel |
| `PLATFORM` | 0 | 0.0% | To be extracted in Phase 3 Capabilities |
| `CANDIDATE-FOR-PLATFORM` | 10 | 6.25% | Extract as platform capability primitives |
| `ADAPTER` | 12 | 7.5% | Wrap behind standardized interfaces |
| `EXAMPLE` | 102 | 63.75% | Retain isolated in `foundation/examples/` |
| `EXPERIMENTAL` | 18 | 11.25% | Quarantine in `foundation/experimental/` |
| `LEGACY` | 8 | 5.0% | Deprecate and queue for Phase 6 sunset |
| `BROKEN` | 4 | 2.5% | Block promotion; remediate if required |
| `DUPLICATE` | 6 | 3.75% | Consolidate duplicate patterns |
| **Total** | **160** | **100.0%** | **Reconciled Master Classification** |

### Lifecycle Status Totals

| Lifecycle Status | Count | Percentage | Definition |
| :--- | :---: | :---: | :--- |
| `EXPERIMENT` | 22 | 13.75% | Early research or unverified browser agent |
| `PROTOTYPE` | 108 | 67.5% | Working reference application example |
| `INTERNAL` | 12 | 7.5% | Internal tool or model store adapter |
| `BETA` | 10 | 6.25% | High-quality candidate for platform |
| `PRODUCTION-CANDIDATE` | 0 | 0.0% | Requires Phase 2 Kernel + Evals |
| `PRODUCTION` | 0 | 0.0% | Requires full release gate review |
| `DEPRECATED` | 8 | 5.0% | Outdated framework syntax |
| **Total** | **160** | **100.0%** | **Reconciled Lifecycle Metrics (22 + 108 + 12 + 10 + 8 = 160)** |

---

## 3. Rationale for Candidate Components (10 Components)

1. `always_on_agents/always_on_hn_briefing_agent`: Clean background runner, APScheduler integration, and scout architecture.
2. `agent_skills/commit-archaeologist`: Structured CLI skill contract with strict input/output bounds.
3. `mcp_ai_agents/multi_mcp_agent`: Multi-server MCP router showcase.
4. `advanced_ai_agents/multi_agent_apps/devpulse_ai`: Clean event-driven multi-agent routing.
5. `rag_tutorials/agentic_typed_rag_pydanticai`: Typed RAG validation using PydanticAI.
6. `agent_skills/evals/scope-creep-detector`: Reusable skill evaluation runner.
7. `generative_ui_agents/ai-mcp-app-builder`: Generative UI app builder widget contract.
8. `advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team`: Dynamic routing multi-agent team.
9. `always_on_agents/release_radar_agent`: Ranker and notification scoring primitives.
10. `starter_ai_agents/xai_finance_agent`: Robust financial data adapter primitives.

---

## 4. Master Classification Table (160 Components)

| Component Path | Primary Classification | Lifecycle Status | Platform Action |
| :--- | :--- | :--- | :--- |
| `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_seo_audit_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_aqi_analysis_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_codebase_migration_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_domain_deep_research_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_negotiation_battle_simulator` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `advanced_ai_agents/multi_agent_apps/ai_speech_trainer_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/devpulse_ai` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `advanced_ai_agents/multi_agent_apps/multi_agent_researcher` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/multi_agent_apps/trust_gated_agent_team` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_agent_governance` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_consultant_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_customer_support_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_deep_research_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_email_gtm_reachout_agent` | DUPLICATE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_health_fitness_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_investment_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_journalist_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_meeting_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_movie_production_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_personal_finance_agent` | DUPLICATE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_startup_insight_fire1_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/ai_system_architect_r1` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_ai_agents/single_agent_apps/windows_use_autonomous_agent` | BROKEN | EXPERIMENT | Quarantine |
| `advanced_llm_apps/chat-with-tarots` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_llm_apps/chat_with_X_tutorials` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_llm_apps/cursor_ai_experiments` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `advanced_llm_apps/gpt_oss_critique_improvement_loop` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_llm_apps/llm_apps_with_memory_tutorials` | LEGACY | DEPRECATED | Retain in foundation |
| `advanced_llm_apps/llm_finetuning_tutorials` | LEGACY | DEPRECATED | Retain in foundation |
| `advanced_llm_apps/llm_optimization_tools` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_llm_apps/multimodal_video_moment_finder` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_llm_apps/resume_job_matcher` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `advanced_llm_apps/thinkpath_chatbot_app` | LEGACY | DEPRECATED | Retain in foundation |
| `agent_skills/advisor-orchestrator-worker` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/commit-archaeologist` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `agent_skills/dependency-doctor` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/evals/advisor-orchestrator-worker` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/evals/commit-archaeologist` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/evals/dependency-doctor` | BROKEN | EXPERIMENT | Quarantine |
| `agent_skills/evals/project-graveyard` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/evals/scope-creep-detector` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `agent_skills/evals/thinking-out-loud` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/evals/tools` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/project-graveyard` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/scope-creep-detector` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/self-improving-agent-skills` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `agent_skills/thinking-out-loud` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/2_model_agnostic_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/3_structured_output_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent` | BROKEN | EXPERIMENT | Quarantine |
| `ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/6_callbacks` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/7_plugins` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/8_simple_multi_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/9_multi_agent_patterns` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/10_tracing_observability` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/11_voice` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/2_structured_output_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/3_tool_using_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/4_running_agents` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/5_context_management` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/8_handoffs_delegation` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/9_multi_agent_orchestration` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `always_on_agents/always_on_hn_briefing_agent` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `always_on_agents/release_radar_agent` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `generative_ui_agents/ai-dashboard-canvas-agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `generative_ui_agents/ai-deep-research-agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `generative_ui_agents/ai-financial-coach-agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `generative_ui_agents/ai-knowledge-explorer` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `generative_ui_agents/ai-mcp-app-builder` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `generative_ui_agents/ai-shadcn-component-generator` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `generative_ui_agents/generative-ui-starter-project` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `generative_ui_agents/mcp-apps-generative-ui-showcase` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `mcp_ai_agents/ai_travel_planner_mcp_agent_team` | DUPLICATE | PROTOTYPE | Retain in foundation |
| `mcp_ai_agents/browser_mcp_agent` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `mcp_ai_agents/github_mcp_agent` | ADAPTER | INTERNAL | Retain in foundation |
| `mcp_ai_agents/multi_mcp_agent` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `mcp_ai_agents/multi_mcp_agent_router` | ADAPTER | INTERNAL | Retain in foundation |
| `mcp_ai_agents/notion_mcp_agent` | ADAPTER | INTERNAL | Retain in foundation |
| `mcp_ai_agents/openai_remote_mcp_bridge` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `rag_tutorials/agentic_rag_embedding_gemma` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/agentic_rag_gpt5` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `rag_tutorials/agentic_rag_math_agent` | BROKEN | EXPERIMENT | Quarantine |
| `rag_tutorials/agentic_rag_with_reasoning` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `rag_tutorials/agentic_typed_rag_pydanticai` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `rag_tutorials/ai_blog_search` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `rag_tutorials/autonomous_rag` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `rag_tutorials/contextualai_rag_agent` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/corrective_rag` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/deepseek_local_rag_agent` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `rag_tutorials/gemini_agentic_rag` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `rag_tutorials/hybrid_search_rag` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/knowledge_graph_rag_citations` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/llama3.1_local_rag` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `rag_tutorials/local_hybrid_search_rag` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/local_rag_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `rag_tutorials/multimodal_agentic_rag` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/qwen_local_rag` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `rag_tutorials/rag-as-a-service` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `rag_tutorials/rag_agent_cohere` | LEGACY | DEPRECATED | Retain in foundation |
| `rag_tutorials/rag_chain` | LEGACY | DEPRECATED | Retain in foundation |
| `rag_tutorials/rag_database_routing` | ADAPTER | INTERNAL | Retain in foundation |
| `rag_tutorials/rag_failure_diagnostics_clinic` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `rag_tutorials/vision_rag` | ADAPTER | INTERNAL | Retain in foundation |
| `starter_ai_agents/ai_blog_to_podcast_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_breakup_recovery_agent` | DUPLICATE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_data_analysis_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_data_visualisation_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_life_insurance_advisor_agent` | DUPLICATE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_medical_imaging_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_meme_generator_agent_browseruse` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `starter_ai_agents/ai_music_generator_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_reasoning_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_startup_trend_analysis_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_travel_agent` | DUPLICATE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/ai_x402_paying_agent` | LEGACY | DEPRECATED | Retain in foundation |
| `starter_ai_agents/mixture_of_agents` | LEGACY | DEPRECATED | Retain in foundation |
| `starter_ai_agents/multimodal_ai_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/openai_research_agent` | LEGACY | DEPRECATED | Retain in foundation |
| `starter_ai_agents/web_scraping_ai_agent` | EXAMPLE | PROTOTYPE | Retain in foundation |
| `starter_ai_agents/xai_finance_agent` | CANDIDATE-FOR-PLATFORM | BETA | Extract in Phase 3 |
| `voice_ai_agents/ai_audio_tour_agent` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `voice_ai_agents/customer_support_voice_agent` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `voice_ai_agents/insurance_claim_live_agent_team` | EXPERIMENTAL | EXPERIMENT | Quarantine |
| `voice_ai_agents/voice_rag_openaisdk` | EXPERIMENTAL | EXPERIMENT | Quarantine |
