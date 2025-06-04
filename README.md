# Co-Parent Filter Bot

A production-ready Telegram bot that monitors messages from a specific user in a group and filters them based on co-parenting topics using AI with detailed behavioral analysis and targeted feedback.

## Features

- **Smart User Monitoring**: Tracks messages from a configurable target user
- **AI-Powered Classification**: Uses OpenAI GPT-4o with detailed reasoning
- **Behavioral Profile Matching**: Configurable moderation profiles for different personality types
- **Targeted Feedback**: Provides specific explanations for why messages are blocked
- **Permissive Mode**: Only blocks obviously problematic content, allows ambiguous messages
- **Detailed Logging**: Comprehensive logs with decision reasoning and categories
- **Easy Deployment**: Production-ready with systemd service

## Moderation Profiles

### Manipulative Co-Parent Profile

Designed for users who exhibit:

- Performative posturing without follow-through
- Crafting narratives about being good while failing to take action
- Manipulative language designed to appear reasonable
- Deflection from logistics to emotional manipulation
- Making themselves appear as victim or hero
- Saying the right things but consistently failing to act
- Using guilt, blame, or emotional pressure instead of facts
- Grandstanding or virtue signaling without substance

### How It Works

The bot analyzes messages for these specific behavioral patterns and provides targeted feedback like:

- "This appears to be performative posturing rather than actionable co-parenting communication"
- "This message deflects from logistics to emotional manipulation"
- "This seems designed to craft a narrative rather than address children's needs"

## Prerequisites

### 1. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` command and follow instructions
3. Save the `BOT_TOKEN` provided
4. Use `/setprivacy` command and select your bot
5. Choose "Disable" to allow the bot to read all group messages

### 2. Add Bot to Group

1. Add your bot to the target Telegram group
2. Promote the bot to admin with "Delete messages" permission
3. Note: The bot needs admin rights to delete messages

### 3. Get OpenAI API Key

1. Sign up at [OpenAI](https://platform.openai.com/)
2. Generate an API key from the dashboard
3. Ensure you have sufficient credits for API usage

## Local Development

### Setup

```bash
# Clone repository
git clone <your-repo-url>
cd co_parent_filter_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your values
```

### Configuration

Edit `.env` file with your credentials:

```
BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
TARGET_USERNAME=parkerrralex
MODERATION_PROFILE=manipulative_coparent
```

### Run Locally

```bash
python -m bot.main
```

The bot will start and begin monitoring messages. Check the console for detailed logs.

## Bot Commands

- `/start` - Show bot status and current configuration
- `/status` - Display detailed bot status and settings
- `/profile` - Show current moderation profile and behavioral patterns being monitored

## Production Deployment (EC2)

### 1. Launch EC2 Instance

- Use Ubuntu 22.04 LTS or Amazon Linux 2023
- t3.micro is sufficient for moderate usage
- Configure security group to allow outbound traffic on ports 443/80 only

### 2. Server Setup

```bash
# Connect via SSH
ssh -i your-key.pem ec2-user@your-instance-ip

# Update system and install dependencies
# For Ubuntu/Debian:
sudo apt-get update && sudo apt-get install -y git python3-venv

# For Amazon Linux 2023:
sudo dnf update -y && sudo dnf install -y git python3-pip python3-venv

# For Amazon Linux 2 (older):
sudo yum update -y && sudo yum install -y git python3-pip python3-venv

# Check your OS version if unsure:
cat /etc/os-release

# Clone and setup project
git clone <your-repo-url>
cd co_parent_filter_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your production values
nano .env
```

### 3. Install Systemd Service

```bash
# Copy service file
sudo cp deployment/coparentbot.service /etc/systemd/system/

# Update service file paths if needed
sudo nano /etc/systemd/system/coparentbot.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable --now coparentbot

# Check status
sudo systemctl status coparentbot
sudo journalctl -u coparentbot -f
```

### 4. Verify Deployment

- Check logs with: `sudo journalctl -u coparentbot -f`
- Test message filtering in your Telegram group
- Monitor for any errors or issues

## Configuration

### Environment Variables

- `BOT_TOKEN`: Telegram bot token from BotFather
- `OPENAI_API_KEY`: OpenAI API key for GPT-4o
- `TARGET_USERNAME`: Username to monitor (without @)
- `MODERATION_PROFILE`: Behavioral profile to use (`manipulative_coparent` or `standard`)

### Available Moderation Profiles

#### `manipulative_coparent`

- **Purpose**: Monitor for performative behavior and manipulation
- **Mode**: Permissive (only blocks obvious violations)
- **Feedback**: Targeted responses about specific behavioral patterns
- **Best for**: Co-parents with history of narrative crafting and inconsistent actions

#### `standard`

- **Purpose**: Basic co-parenting topic filtering
- **Mode**: Permissive
- **Feedback**: Generic topic-based responses
- **Best for**: General message filtering without behavioral analysis

### Updating Configuration

You can change settings without code changes:

```bash
# Method 1: Edit .env file
nano .env
# Change TARGET_USERNAME=new_username or MODERATION_PROFILE=standard

# Method 2: Export environment variable
export TARGET_USERNAME=new_username
export MODERATION_PROFILE=standard

# Restart service
sudo systemctl restart coparentbot
```

## AI Response Format

The bot now returns detailed JSON responses:

```json
{
  "allow": true/false,
  "reason": "Specific explanation for the decision",
  "category": "classification_category"
}
```

Example responses:

- `{"allow": true, "reason": "Legitimate scheduling discussion", "category": "scheduling"}`
- `{"allow": false, "reason": "This appears to be performative posturing rather than actionable co-parenting communication", "category": "performative"}`

## Swapping AI Models

To replace OpenAI with a cheaper LLM provider, modify only `bot/filters.py`:

### Example: Replace with HTTP API

```python
def classify(text: str) -> ModerationResponse:
    """Replace OpenAI call with HTTP request to another service."""
    import requests

    system_prompt = _build_system_prompt()

    response = requests.post(
        "https://api.example.com/classify",
        json={
            "text": text,
            "system_prompt": system_prompt,
            "task": "detailed_coparenting_filter"
        },
        headers={"Authorization": "Bearer YOUR_API_KEY"}
    )

    result = response.json()
    return ModerationResponse.from_json(json.dumps(result))
```

### Supported Providers

The `classify()` function can be easily adapted for:

- Together AI
- Groq
- Mistral API
- Cohere
- Local models via Ollama
- Any HTTP API returning detailed JSON responses

## Hardening & Security

### Production Security

1. **Dedicated User**: Run bot under dedicated Linux user

   ```bash
   sudo useradd -r -s /bin/false coparentbot
   sudo chown -R coparentbot:coparentbot /path/to/bot
   ```

2. **Firewall**: Use ufw to restrict network access

   ```bash
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow ssh
   sudo ufw enable
   ```

3. **Secrets Management**: Store sensitive data in AWS Parameter Store or Secrets Manager instead of plain .env files

### API Key Security

- Use environment variables instead of hardcoded keys
- Rotate API keys regularly
- Monitor API usage for anomalies
- Set up billing alerts for OpenAI usage

## Monitoring & Maintenance

### Logs

- Application logs: `sudo journalctl -u coparentbot -f`
- System logs: `sudo journalctl -xe`
- Log rotation is handled automatically by systemd

### Enhanced Logging

The bot now provides detailed logs including:

- Decision reasoning and categories
- Behavioral pattern detection
- Specific feedback sent to users
- Performance metrics

Example log entry:

```
[2024-01-15T10:30:45] @username: 'I always do everything for the kids...' -> BLOCK (performative): This appears to be performative posturing rather than actionable co-parenting communication
```

### Health Checks

- Monitor systemd service status
- Check API quota usage
- Monitor response times and error rates
- Review moderation accuracy and user feedback

### Updates

```bash
# Pull latest changes
git pull origin main

# Restart service
sudo systemctl restart coparentbot
```

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check bot permissions in group
2. **API errors**: Verify OpenAI API key and quota
3. **Permission denied**: Ensure bot has "Delete messages" admin right
4. **Service won't start**: Check paths in systemd service file
5. **Incorrect moderation**: Verify moderation profile settings

### Debug Mode

Run locally with verbose logging:

```bash
python -m bot.main --debug
```

### Testing Moderation

Use the test script to verify setup:

```bash
python test_setup.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
