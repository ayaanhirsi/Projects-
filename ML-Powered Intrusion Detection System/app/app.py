"""Discord webhook alerts for malicious flows (single-flow and batch summary)."""
from discord_webhook import DiscordWebhook, DiscordEmbed

from app.config import DISCORD_WEBHOOK_URL


def _send(webhook: DiscordWebhook) -> None:
    try:
        webhook.execute()
    except Exception:
        pass  # alerting must never break the API


def send_flow_alert(flow: dict, attack_type: str, reputation: dict, geo: dict) -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    hook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    embed = DiscordEmbed(title="🚨 Intrusion Detected", color="ff0000")
    embed.add_embed_field(name="Source IP", value=flow["src_ip"], inline=False)
    embed.add_embed_field(name="Destination IP", value=flow["dst_ip"], inline=False)
    embed.add_embed_field(name="Attack Type", value=str(attack_type), inline=False)
    embed.add_embed_field(
        name="Location Info",
        value=f"Country: {geo['country']}\nCity: {geo['city']}\nOrg: {geo['org']}",
        inline=False,
    )
    embed.add_embed_field(
        name="AbuseIPDB Scoring",
        value=f"Reputation Score: {reputation['abuse_score']}",
        inline=False,
    )
    hook.add_embed(embed)
    _send(hook)


def send_batch_summary(total: int, threats: int, top_ips: list) -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    hook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    embed = DiscordEmbed(title="📊 Batch Analysis Summary", color="ffa500")
    embed.add_embed_field(name="Flows analyzed", value=str(total))
    embed.add_embed_field(name="Threats identified", value=str(threats))
    embed.add_embed_field(name="Top malicious IPs",
                          value="\n".join(top_ips) or "None", inline=False)
    hook.add_embed(embed)
    _send(hook)
