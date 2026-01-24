import os
import sys
import logging
import datetime
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Configure logging to capture everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Silence some noisy loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Override default config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "deepseek"
config["deep_think_llm"] = "deepseek-coder" # Or whatever the valid model name is, usually implied by provider, but let's be safe
config["quick_think_llm"] = "deepseek-chat"
config["max_debate_rounds"] = 3 # "深度3" usually implies iterations
config["research_iterations"] = 3

# IMPORTANT: Ensure online tools are enabled for real data
config["online_tools"] = True
config["online_news"] = True
config["realtime_data"] = True

print("--- AUDIT START: CONFIG ---")
print(config)
print("--- AUDIT END: CONFIG ---")

print("--- AUDIT START: INITIALIZATION ---")
try:
    ta = TradingAgentsGraph(debug=True, config=config)
    print("Graph initialized successfully.")
except Exception as e:
    print(f"Graph initialization failed: {e}")
    sys.exit(1)
print("--- AUDIT END: INITIALIZATION ---")

target_symbol = "01810.HK"
target_date = datetime.datetime.now().strftime("%Y-%m-%d")

print(f"--- AUDIT START: PROPAGATION ({target_symbol} @ {target_date}) ---")
try:
    final_state, decision = ta.propagate(target_symbol, target_date)
    print("\n=== FINAL DECISION ===")
    print(decision)
except Exception as e:
    print(f"Propagation failed: {e}")
    import traceback
    traceback.print_exc()

print("--- AUDIT END: PROPAGATION ---")
