# Attack Strategy Integration

## Overview

This document describes the integration of attack strategies into the red team evaluator agents' conversation flow. The implementation enables automatic, context-aware attack enhancement of messages sent to evaluated agents during red team testing.

## Implementation Summary

Attack strategies are now seamlessly integrated into the red team evaluator agents' conversation flow. When the evaluator agent generates a message to test a target agent, the system automatically enhances it with appropriate attack techniques based on the OWASP category being tested.

## Key Changes

### 1. Attack Enhancement in Red Team Evaluators

Both `RedTeamA2AEvaluatorAgent` and `RedTeamMCPEvaluatorAgent` now include:

- **OWASP Framework Loading**: Loads the OWASP framework on initialization to access attack classes
- **Scenario Context Tracking**: Tracks which scenario is being tested for each conversation context
- **Message Enhancement Override**: Overrides `_send_message_to_evaluated_agent` to enhance messages before sending

### 2. Attack Selection Strategy

The attack selection follows a sophisticated strategy:

- **70% Enhancement Probability**: 70% chance to enhance messages with attacks, 30% chance to send raw messages (for natural variation)
- **Context-Aware Selection**: Selects attacks based on the OWASP category being tested
- **Weighted Selection**: Attacks are weighted by their `weight` property (higher weight = more likely to be selected)
- **Fallback Mechanism**: Falls back to random category selection if scenario tracking fails

### 3. Scenario Tracking

The system tracks scenarios for better attack selection:

- **Context-to-Scenario Mapping**: Maps conversation contexts to their associated scenarios
- **OWASP Category Extraction**: Extracts OWASP category IDs from scenario text/expected_outcome
- **Evaluation Logging Override**: Overrides `_log_evaluation` to track scenarios for better attack selection

## How It Works

### Flow Diagram

```
1. LLM generates message
   ↓
2. _send_message_to_evaluated_agent intercepts
   ↓
3. Check if attack enhancement should be applied (70% probability)
   ↓
4. Identify OWASP category from current scenario
   ↓
5. Select attack from category's attack list (weighted by attack weight)
   ↓
6. Attack's enhance() method transforms the message
   ↓
7. Enhanced message sent to evaluated agent
```

### Code Example

```python
# In RedTeamA2AEvaluatorAgent or RedTeamMCPEvaluatorAgent

async def _send_message_to_evaluated_agent(
    self,
    context_id: str,
    message: str,
) -> dict[str, str]:
    """
    Send message to evaluated agent with attack enhancement.
    """
    # Enhance message with attack if applicable
    enhanced_message = self._select_and_enhance_attack(message, context_id)
    
    # Call parent method with enhanced message
    return await super()._send_message_to_evaluated_agent(
        context_id,
        enhanced_message,
    )
```

### Attack Selection Logic

```python
def _select_and_enhance_attack(
    self,
    message: str,
    context_id: str,
) -> str:
    """
    Select an appropriate attack and enhance the message.
    
    Strategy:
    - 70% chance to enhance with an attack
    - 30% chance to send raw message
    - Select attack based on scenario's OWASP category
    - Weight attacks by their weight property
    """
    # 70% probability check
    if random.random() > 0.7:
        return message
    
    # Extract OWASP category from scenario
    category_id = self._extract_owasp_category_from_scenario(scenario_text)
    
    # Get attacks for this category
    attacks = self._get_attacks_for_category(category_id)
    
    # Create weighted list
    weighted_attacks = []
    for attack in attacks:
        weight = getattr(attack, "weight", 1)
        weighted_attacks.extend([attack] * weight)
    
    # Select random attack from weighted list
    selected_attack = random.choice(weighted_attacks)
    
    # Enhance message
    enhanced_message = selected_attack.enhance(message)
    return enhanced_message
```

## Benefits

### 1. Natural Integration
- Attacks are applied automatically without manual intervention
- The LLM evaluator agent doesn't need to know about attack techniques
- Attacks feel natural and integrated into the conversation flow

### 2. Context-Aware
- Attacks are selected based on the OWASP category being tested
- Different attack strategies for different vulnerability types
- More effective testing by matching attacks to vulnerabilities

### 3. Weighted Selection
- Higher-weight attacks are more likely to be used
- Allows prioritizing more effective attack techniques
- Configurable attack importance through weight property

### 4. Probabilistic Enhancement
- Not every message is enhanced, making conversations feel natural
- Mix of enhanced and raw messages prevents detection
- More realistic attack scenarios

### 5. Protocol-Agnostic
- Works for both A2A and MCP protocols
- Same attack logic for all communication protocols
- Consistent behavior across different agent types

## Attack Classes

The following attack classes are available for enhancement:

### Single-Turn Attacks

- **PromptInjection**: Injects adversarial instructions to override system behavior
- **Base64**: Encodes messages in Base64 to bypass text filters
- **ROT13**: Encodes messages using ROT13 cipher
- **Leetspeak**: Transforms messages using leetspeak encoding
- **PromptProbing**: Asks probing questions to extract system information
- **Roleplay**: Adopts a privileged persona to bypass restrictions

### Attack Weights

Attacks have a `weight` property that determines their selection probability:

- **Weight 3**: High priority attacks (e.g., PromptInjection for LLM_01)
- **Weight 2**: Medium priority attacks (e.g., Base64, ROT13)
- **Weight 1**: Low priority attacks (used as fallback)

## OWASP Category Mapping

### LLM_01: Prompt Injection
- **Attacks**: PromptInjection (weight=3), Base64, ROT13, Leetspeak, Roleplay, PromptProbing
- **Focus**: Instruction override attacks

### LLM_06: Excessive Agency
- **Attacks**: Roleplay (weight=3), PromptInjection, PromptProbing
- **Focus**: Unauthorized actions and privilege escalation

### LLM_07: System Prompt Leakage
- **Attacks**: PromptInjection, PromptProbing, Base64, ROT13
- **Focus**: Prompt extraction and information disclosure

## Configuration

### Enabling Attack Enhancement

Attack enhancement is automatically enabled when:

1. `evaluation_mode` is set to `EvaluationMode.RED_TEAM`
2. `owasp_categories` are provided in the `AgentConfig`
3. Red team evaluator agents are instantiated

### Disabling Attack Enhancement

To disable attack enhancement, use the standard evaluator agents instead of red team evaluator agents:

```python
# Standard evaluator (no attack enhancement)
agent = A2AEvaluatorAgent(...)

# Red team evaluator (with attack enhancement)
agent = RedTeamA2AEvaluatorAgent(
    owasp_categories=["LLM_01", "LLM_06"],
    ...
)
```

## Testing

### Manual Testing

To test attack enhancement:

1. Start a target agent (e.g., t-shirt store example)
2. Run red team evaluation with OWASP categories
3. Observe enhanced messages in the conversation logs
4. Check for attack names in debug logs

### Debug Logging

Attack enhancement logs debug information:

```
🔴 Enhanced message with attack
  - attack_name: PromptInjection
  - category_id: LLM_01
  - context_id: abc123...
  - original_length: 50
  - enhanced_length: 200
```

## Future Enhancements

Potential improvements:

1. **Multi-Turn Attacks**: Support for attacks that span multiple messages
2. **Adaptive Selection**: Learn which attacks are most effective and adjust weights
3. **Attack Chaining**: Combine multiple attacks in sequence
4. **Custom Attack Weights**: Allow configuration of attack weights per category
5. **Attack Success Tracking**: Track which attacks successfully exploit vulnerabilities

## Related Files

- `rogue/evaluator_agent/red_team_a2a_evaluator_agent.py`: A2A red team evaluator with attack enhancement
- `rogue/evaluator_agent/red_team_mcp_evaluator_agent.py`: MCP red team evaluator with attack enhancement
- `rogue/server/red_teaming/attacks/`: Attack class implementations
- `rogue/server/red_teaming/frameworks/owasp/`: OWASP framework and category definitions

## References

- [OWASP Top 10 for LLMs](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Attack Classes Documentation](./ATTACK_CLASSES.md) (if exists)
- [Red Teaming Guide](./RED_TEAMING_GUIDE.md) (if exists)
