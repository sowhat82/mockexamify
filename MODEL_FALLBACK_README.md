# OpenRouter Model Fallback Configuration

## Overview
The OpenRouter integration now supports automatic cascading fallback through multiple AI models. If one model fails or is unavailable, the system automatically tries the next model in the priority list.

## Configuration File: `models_config.json`

The model priority is defined in `models_config.json`:

```json
{
  "models": [
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "mistralai/mixtral-8x7b-instruct",
    "openai/gpt-4o-mini"
  ]
}
```

## How It Works

1. **Primary Model (Try First)**: `meta-llama/llama-3.3-70b-instruct:free`
   - Free tier Llama 3.3 70B model
   - High quality, no cost

2. **Backup 1**: `mistralai/mistral-7b-instruct:free`
   - Free tier Mistral 7B
   - Good quality, no cost

3. **Backup 2**: `mistralai/mixtral-8x7b-instruct`
   - Paid Mixtral 8x7B
   - Higher quality, small cost

4. **Final Fallback**: `openai/gpt-4o-mini`
   - Reliable GPT-4o mini
   - Guaranteed availability, small cost

## Fallback Logic

When an API call is made:
1. Try model #1 (Llama 3.3)
2. If fails → Try model #2 (Mistral 7B)
3. If fails → Try model #3 (Mixtral 8x7B)
4. If fails → Try model #4 (GPT-4o mini)
5. If all fail → Return error message

## Cost Optimization Strategy

This configuration prioritizes:
- **Free models first** (Llama, Mistral free tier)
- **Paid models as backup** (Mixtral, GPT-4o mini)
- **Maximum reliability** (GPT-4o mini as final fallback)

## Modifying the Model List

To change the model priority order, edit `models_config.json`:

```json
{
  "models": [
    "your-preferred-model/name",
    "your-backup-model/name",
    "final-fallback-model/name"
  ]
}
```

The app will automatically reload the configuration on next restart.

## Logging

The system logs which model is being tried and which model successfully generates content:
- `"Attempting with model 1/4: meta-llama/llama-3.3-70b-instruct:free"`
- `"Successfully generated text using model: meta-llama/llama-3.3-70b-instruct:free"`
- `"All 4 models failed. Last error: ..."` (if all fail)

Check logs to see model usage patterns and identify any issues.
