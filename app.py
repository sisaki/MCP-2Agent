from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from orchestrator import orchestrate, load_rows, detect_intent

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    try:
        data = request.json
        query = data.get('query', '').strip()
        intent = data.get('intent', None)  # Optional explicit intent
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Detect intent if not provided (with history context)
        if intent is None:
            rows = load_rows()
            history = rows[-5:] if len(rows) > 5 else rows
            intent = detect_intent(query, history)
        
        # Run orchestration (only executes requested stage)
        result = orchestrate(query, intent)
        
        # Get executed stages from orchestrator (set by LLM planning)
        executed_stages = result.get('_executed_stages', [])
        planned_stages = result.get('_planned_stages', [])
        
        # Get last 5 messages for context display
        rows = load_rows()
        last_5_messages = rows[-5:] if len(rows) > 5 else rows
        
        # Only return data for executed stages (not cached/previous results)
        response_data = {
            'success': True,
            'query': result['query'],
            'turn': result['turn'],
            'intent': intent,
            'planned_stages': planned_stages,
            'executed_stages': executed_stages,
            'last_5_messages': last_5_messages,
        }
        
        # Only include results for stages that were actually executed in this turn
        if 'search' in executed_stages:
            response_data['search_results'] = result.get('search_results', '')
            response_data['search_confidence'] = result.get('search_confidence', '')
        
        if 'summary' in executed_stages:
            response_data['summary'] = result.get('summary', '')
            response_data['summary_confidence'] = result.get('summary_confidence', '')
            # Expose the messages being summarized for UI
            response_data['summarizing_messages'] = result.get('_summarizing_messages', [])
        
        # Handle conversation queries
        if 'conversation_query' in executed_stages:
            response_data['conversation_response'] = result.get('_conversation_response', result.get('summary', ''))
            response_data['summary'] = result.get('_conversation_response', result.get('summary', ''))
            response_data['summary_confidence'] = result.get('summary_confidence', '1.0')
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        rows = load_rows()
        # Return all conversations (no limit)
        return jsonify({'success': True, 'history': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
