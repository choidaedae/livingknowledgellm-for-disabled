# Evaluation Guide for Prometheus Model

This guide explains how to use the `evaluation_load_json.py` script to evaluate responses using the Prometheus model. The script processes JSON files containing evaluation data and outputs feedback and scores for each scenario.

---

## **1. Prerequisites**

Ensure you have:
- Python 3 installed
- Required Python libraries (`prometheus_eval`, `argparse`, `json`) installed

```bash
conda create -n prometheus python==3.9
conda activate prometheus
pip install prometheus-eval
```
- JSON files with the correct structure stored in the `./conversations` directory

---

## **2. JSON File Structure**

Each JSON file should contain the following keys:
- **instructions**: List of instructions for evaluating the responses.
- **responses**: List of response strings for each scenario.
- **reference_answers**: Ideal reference answers repeated for each scenario.
- **rubric_data**: Dictionary defining the evaluation criteria and score descriptions.

### Example JSON Structure:

```json
{
    "instructions": [
        "Evaluate the assistant's ability to engage empathetically and provide appropriate responses."
    ],
    "responses": [
        "User: How are you?\nAssistant: I'm fine, thank you. How about you?"
    ],
    "reference_answers": [
        "User: How are you?\nAssistant: I'm doing well, thank you. How can I assist you today?"
    ],
    "rubric_data": {
        "criteria": "Does the assistant provide natural and empathetic interaction?",
        "score1_description": "Fails to provide natural interaction.",
        "score2_description": "Struggles with empathy or naturalness.",
        "score3_description": "Provides adequate interaction.",
        "score4_description": "Shows strong empathy with minor lapses.",
        "score5_description": "Excels in empathetic and natural interaction."
    }
}
```

Save the JSON files in the `./conversations` directory.

---

## **3. Running the Evaluation Script**

To run the script, execute the following command:

```bash
python evaluation_load_json.py --json_file ./conversations/<file_name>.json
```

### **Arguments**
- `--json_file`: Path to the JSON file to evaluate.

Example:

```bash
python evaluation_load_json.py --json_file ./conversations/conversation_v1.json
```

---

## **4. Script Outputs**

The script outputs:
1. **Feedback**: Detailed analysis of each scenario.
2. **Scores**: Numerical scores (1 to 5) for each scenario.

### Example Output:

```plaintext
Evaluation Results:
Scenario 1:
  Feedback: The assistant maintained a natural and empathetic conversation with the user but missed addressing key context-specific concerns.
  Score: 4
Scenario 2:
  Feedback: The assistant struggled to empathize and provide actionable suggestions.
  Score: 3
```

---

## **5. Evaluation Results Summary**

The average scores for different conversation versions are as follows:

| **Version** | **Average Score** |
|-------------|-------------------|
| V1          | 4.125             |
| V2.1        | 3.125             |
| **V2.2 (Best)**        | **4.375**             |
| V2.3        | 4.0               |

---

## **6. Next Steps**

1. Prepare your JSON files with conversation data.
2. Execute the script for each JSON file.
3. Record the feedback and scores.
4. Use the average scores to analyze and compare the performance of different response styles.

Feel free to reach out for any clarifications or additional support! 😊