import asyncio
from scrapers.telegram_scraper import scrape
from ml.cti_classifier import predict_messages
from utils.exa_helpers import cross_validate_with_exa, search_cyber_threats
from crew import CyberThreatIntelCrew


def run_full_pipeline():
    """
    Runs both pipelines sequentially:
    1. Telegram + Exa Cross-Validation
    2. Exa.ai Threat Search
    """

    # ──────────────────────────────────────
    # PIPELINE 1: Telegram + Exa Cross-Validation
    # ──────────────────────────────────────
    print("\n🚀 Starting Telegram + Exa Cross-Validation Pipeline...\n")

    df, _ = asyncio.get_event_loop().run_until_complete(scrape())
    preds = predict_messages(df["Content"].tolist())
    df["Predicted_Label"] = preds
    cti_messages = df[df["Predicted_Label"] == "CTI"]["Content"].tolist()

    if not cti_messages:
        print("⚠️ No CTI messages found from Telegram.")
    else:
        validated = cross_validate_with_exa(cti_messages, top_n=10)

        # Print for transparency
        print("\n================= TOP 10 SELECTED CTI MESSAGES =================\n")
        for idx, item in enumerate(validated, 1):
            print(f"{idx}. [{item['status']}] {item['message'][:200]}")
            print(f"   → Exa Result: {'FOUND' if item['exa_results'] != 'No external validation found' else 'NOT FOUND'}\n")
        print("===============================================================\n")

        # Combine into one multi-threat Crew run
        inputs_cross = {
            "topic": "Telegram Cross-Validation: Weekly Top 10 CTI Messages (Validated via Exa.ai)",
            "exa_results": "\n\n".join([
                f"{idx+1}. {item['status']} - {item['message']}\n{item['exa_results']}"
                for idx, item in enumerate(validated)
            ]),
            "threat_summary": "",
            "cve_analysis": "",
            "mitigation_strategies": ""
        }

        crew_instance = CyberThreatIntelCrew()
        CyberThreatIntelCrew().kickoff_with_context(inputs=inputs_cross, context={"topic": inputs_cross["topic"]})

    # ──────────────────────────────────────
    # PIPELINE 2: Exa.ai Threat Search
    # ──────────────────────────────────────
    print("\n🌐 Starting Exa.ai Threat Intelligence Pipeline...\n")

    exa_results = search_cyber_threats("latest verified cybersecurity threats")

    inputs_exa = {
        "topic": "Latest cybersecurity threats September 2025",
        "exa_results": exa_results,
        "threat_summary": "",
        "cve_analysis": "",
        "mitigation_strategies": ""
    }

    crew_instance = CyberThreatIntelCrew()
    CyberThreatIntelCrew().kickoff_with_context(inputs=inputs_exa, context={"topic": inputs_exa["topic"]})


if __name__ == "__main__":
    run_full_pipeline()
