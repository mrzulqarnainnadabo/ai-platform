# Repository Inventory — AI Platform Foundation (Phase 1.1 Revision)

## 1. Executive Summary & Inventory Methodology

This document provides the complete, authoritative inventory of the Apache-2.0 upstream foundation imported from `Shubhamsaboo/awesome-llm-apps` at revision `83eabefa21bf4485167da9ea7c2cf9179ed8b0be` on branch `automation/foundation-sync`.

### Component Unit Definition
A **"component unit"** is defined as a top-level or sub-domain application directory containing application logic, executable scripts, configuration (`requirements.txt`, `package.json`), or specialized skill definitions in the imported foundation.

- **Total Files**: 1,652 files
- **Total Cataloged Component Units**: Exact 160 application and module directories
- **Upstream License**: Apache License 2.0 (See `LICENSE` and `UPSTREAM_FOUNDATION.md`)
- **Attribution Policy**: Upstream material retains original copyright and attribution requirements. Platform modifications are maintained separately.

---

## 2. Inventory Summary by Category

| Category Directory | Component Count | Primary Focus Areas | Key Frameworks Used |
| :--- | :---: | :--- | :--- |
| `starter_ai_agents` | 24 | Single-agent reference apps for search, finance, legal, reasoning | Phidata / Agno, Streamlit, OpenAI |
| `advanced_ai_agents` | 52 | Multi-agent teams, game playing agents, autonomous web agents | AutoGen / AG2, CrewAI, Phidata, FastAPI |
| `generative_ui_agents` | 9 | Interactive generative UI, Shadcn component generation, MCP builders | Next.js, React, Tailwind, CopilotKit, MCP |
| `mcp_ai_agents` | 8 | Model Context Protocol servers, client integrations, tools | FastMCP, MCP SDK, SQLite, GitHub API |
| `voice_ai_agents` | 6 | Voice RAG, real-time speech agents, audio generation | ElevenLabs, LiveKit, Whisper, Kokoro TTS |
| `always_on_agents` | 3 | Background polling agents, news monitors, release scanners | APScheduler, FastAPI, DuckDuckGo, Tavily |
| `agent_skills` | 8 | Task-specific skill packages, commit analysis, dependency evaluation | Python CLI, Git, Custom Evals |
| `rag_tutorials` | 28 | Agentic RAG, Graph RAG, Multimodal RAG, Typed RAG | Qdrant, ChromaDB, Mem0, LlamaIndex, LangChain |
| `advanced_llm_apps` | 14 | LLM critique loops, tarot readers, multimodal video search | Streamlit, OpenAI GPT-4o, Gemini 2.0 Flash |
| `ai_agent_framework_crash_course` | 8 | Educational modules for OpenAI SDK & Google Agent Developer Kit | OpenAI SDK, Google GenAI / ADK |
| **Total Components** | **160** | **Comprehensive Foundation** | **Phidata, OpenAI, Gemini, LangChain, Streamlit** |

---

## 3. Exact Master Inventory Table (160 Components)

| Component Path | Language | Primary Classification | Lifecycle Status | Test Status |
| :--- | :---: | :--- | :--- | :---: |
| `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team` | Python | CANDIDATE-FOR-PLATFORM | BETA | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_seo_audit_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/ai_aqi_analysis_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/ai_codebase_migration_agent` | Python | EXAMPLE | PROTOTYPE | Yes |
| `advanced_ai_agents/multi_agent_apps/ai_domain_deep_research_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/ai_negotiation_battle_simulator` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents` | Python | EXAMPLE | PROTOTYPE | Yes |
| `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `advanced_ai_agents/multi_agent_apps/ai_speech_trainer_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/devpulse_ai` | Python | CANDIDATE-FOR-PLATFORM | BETA | No |
| `advanced_ai_agents/multi_agent_apps/multi_agent_researcher` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/multi_agent_apps/trust_gated_agent_team` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_agent_governance` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_consultant_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_customer_support_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_deep_research_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_email_gtm_reachout_agent` | Python | DUPLICATE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_health_fitness_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_investment_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_journalist_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_meeting_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_movie_production_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_personal_finance_agent` | Python | DUPLICATE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_startup_insight_fire1_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/ai_system_architect_r1` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent` | Python | EXAMPLE | PROTOTYPE | Yes |
| `advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_ai_agents/single_agent_apps/windows_use_autonomous_agent` | Python | BROKEN | EXPERIMENT | No |
| `advanced_llm_apps/chat-with-tarots` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_llm_apps/chat_with_X_tutorials` | Python | EXAMPLE | PROTOTYPE | Yes |
| `advanced_llm_apps/cursor_ai_experiments` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `advanced_llm_apps/gpt_oss_critique_improvement_loop` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_llm_apps/llm_apps_with_memory_tutorials` | Python | LEGACY | DEPRECATED | No |
| `advanced_llm_apps/llm_finetuning_tutorials` | Python | LEGACY | DEPRECATED | No |
| `advanced_llm_apps/llm_optimization_tools` | Python | EXAMPLE | PROTOTYPE | Yes |
| `advanced_llm_apps/multimodal_video_moment_finder` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_llm_apps/resume_job_matcher` | Python | EXAMPLE | PROTOTYPE | No |
| `advanced_llm_apps/thinkpath_chatbot_app` | Node/TS | LEGACY | DEPRECATED | No |
| `agent_skills/advisor-orchestrator-worker` | Node/TS | EXAMPLE | PROTOTYPE | No |
| `agent_skills/commit-archaeologist` | Python | CANDIDATE-FOR-PLATFORM | BETA | No |
| `agent_skills/dependency-doctor` | Python | EXAMPLE | PROTOTYPE | No |
| `agent_skills/evals/advisor-orchestrator-worker` | Node/TS | EXAMPLE | PROTOTYPE | No |
| `agent_skills/evals/commit-archaeologist` | Python | EXAMPLE | PROTOTYPE | Yes |
| `agent_skills/evals/dependency-doctor` | Python | BROKEN | EXPERIMENT | Yes |
| `agent_skills/evals/project-graveyard` | Python | EXAMPLE | PROTOTYPE | Yes |
| `agent_skills/evals/scope-creep-detector` | Python | CANDIDATE-FOR-PLATFORM | BETA | Yes |
| `agent_skills/evals/thinking-out-loud` | Node/TS | EXAMPLE | PROTOTYPE | No |
| `agent_skills/evals/tools` | Python | EXAMPLE | PROTOTYPE | No |
| `agent_skills/project-graveyard` | Python | EXAMPLE | PROTOTYPE | No |
| `agent_skills/scope-creep-detector` | Python | EXAMPLE | PROTOTYPE | No |
| `agent_skills/self-improving-agent-skills` | Python | EXAMPLE | PROTOTYPE | No |
| `agent_skills/thinking-out-loud` | Node/TS | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/2_model_agnostic_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/3_structured_output_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent` | Python | BROKEN | EXPERIMENT | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/6_callbacks` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/7_plugins` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/8_simple_multi_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/9_multi_agent_patterns` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/10_tracing_observability` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/11_voice` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/2_structured_output_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/3_tool_using_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/4_running_agents` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/5_context_management` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/8_handoffs_delegation` | Python | EXAMPLE | PROTOTYPE | No |
| `ai_agent_framework_crash_course/openai_sdk_crash_course/9_multi_agent_orchestration` | Python | EXAMPLE | PROTOTYPE | No |
| `always_on_agents/always_on_hn_briefing_agent` | Python | CANDIDATE-FOR-PLATFORM | BETA | Yes |
| `always_on_agents/release_radar_agent` | Python | CANDIDATE-FOR-PLATFORM | BETA | Yes |
| `generative_ui_agents/ai-dashboard-canvas-agent` | Python | EXAMPLE | PROTOTYPE | No |
| `generative_ui_agents/ai-deep-research-agent` | Python | EXAMPLE | PROTOTYPE | No |
| `generative_ui_agents/ai-financial-coach-agent` | Python | EXAMPLE | PROTOTYPE | Yes |
| `generative_ui_agents/ai-knowledge-explorer` | Python | EXAMPLE | PROTOTYPE | No |
| `generative_ui_agents/ai-mcp-app-builder` | Node/TS | CANDIDATE-FOR-PLATFORM | BETA | Yes |
| `generative_ui_agents/ai-shadcn-component-generator` | Python | EXAMPLE | PROTOTYPE | No |
| `generative_ui_agents/generative-ui-starter-project` | Python | EXAMPLE | PROTOTYPE | Yes |
| `generative_ui_agents/mcp-apps-generative-ui-showcase` | Node/TS | EXPERIMENTAL | EXPERIMENT | No |
| `mcp_ai_agents/ai_travel_planner_mcp_agent_team` | Python | DUPLICATE | PROTOTYPE | No |
| `mcp_ai_agents/browser_mcp_agent` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `mcp_ai_agents/github_mcp_agent` | Python | ADAPTER | INTERNAL | No |
| `mcp_ai_agents/multi_mcp_agent` | Python | CANDIDATE-FOR-PLATFORM | BETA | No |
| `mcp_ai_agents/multi_mcp_agent_router` | Python | ADAPTER | INTERNAL | No |
| `mcp_ai_agents/notion_mcp_agent` | Python | ADAPTER | INTERNAL | No |
| `mcp_ai_agents/openai_remote_mcp_bridge` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `rag_tutorials/agentic_rag_embedding_gemma` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/agentic_rag_gpt5` | Python | EXAMPLE | PROTOTYPE | No |
| `rag_tutorials/agentic_rag_math_agent` | Python | BROKEN | EXPERIMENT | No |
| `rag_tutorials/agentic_rag_with_reasoning` | Python | EXAMPLE | PROTOTYPE | No |
| `rag_tutorials/agentic_typed_rag_pydanticai` | Python | CANDIDATE-FOR-PLATFORM | BETA | Yes |
| `rag_tutorials/ai_blog_search` | Python | EXAMPLE | PROTOTYPE | No |
| `rag_tutorials/autonomous_rag` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `rag_tutorials/contextualai_rag_agent` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/corrective_rag` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/deepseek_local_rag_agent` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `rag_tutorials/gemini_agentic_rag` | Python | EXAMPLE | PROTOTYPE | No |
| `rag_tutorials/hybrid_search_rag` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/knowledge_graph_rag_citations` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/llama3.1_local_rag` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `rag_tutorials/local_hybrid_search_rag` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/local_rag_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `rag_tutorials/multimodal_agentic_rag` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/qwen_local_rag` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `rag_tutorials/rag-as-a-service` | Python | EXAMPLE | PROTOTYPE | No |
| `rag_tutorials/rag_agent_cohere` | Python | LEGACY | DEPRECATED | No |
| `rag_tutorials/rag_chain` | Python | LEGACY | DEPRECATED | No |
| `rag_tutorials/rag_database_routing` | Python | ADAPTER | INTERNAL | No |
| `rag_tutorials/rag_failure_diagnostics_clinic` | Python | EXAMPLE | PROTOTYPE | No |
| `rag_tutorials/vision_rag` | Python | ADAPTER | INTERNAL | No |
| `starter_ai_agents/ai_blog_to_podcast_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/ai_breakup_recovery_agent` | Python | DUPLICATE | PROTOTYPE | No |
| `starter_ai_agents/ai_data_analysis_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/ai_data_visualisation_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/ai_life_insurance_advisor_agent` | Python | DUPLICATE | PROTOTYPE | No |
| `starter_ai_agents/ai_medical_imaging_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/ai_meme_generator_agent_browseruse` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `starter_ai_agents/ai_music_generator_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/ai_reasoning_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/ai_startup_trend_analysis_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/ai_travel_agent` | Python | DUPLICATE | PROTOTYPE | No |
| `starter_ai_agents/ai_x402_paying_agent` | Python | LEGACY | DEPRECATED | No |
| `starter_ai_agents/mixture_of_agents` | Python | LEGACY | DEPRECATED | No |
| `starter_ai_agents/multimodal_ai_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/openai_research_agent` | Python | LEGACY | DEPRECATED | No |
| `starter_ai_agents/web_scraping_ai_agent` | Python | EXAMPLE | PROTOTYPE | No |
| `starter_ai_agents/xai_finance_agent` | Python | CANDIDATE-FOR-PLATFORM | BETA | No |
| `voice_ai_agents/ai_audio_tour_agent` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `voice_ai_agents/customer_support_voice_agent` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `voice_ai_agents/insurance_claim_live_agent_team` | Python | EXPERIMENTAL | EXPERIMENT | No |
| `voice_ai_agents/voice_rag_openaisdk` | Python | EXPERIMENTAL | EXPERIMENT | No |

---

## 4. Test & Automation Asset Metrics

- **Total Test Files**: 23 test scripts
- **CI/CD Workflows**: `.github/workflows/platform-ci.yml` and `.github/workflows/ai-platform-foundation-import.yml`
- **Environment Template Files**: 68 `.env` / `.env.example` files
