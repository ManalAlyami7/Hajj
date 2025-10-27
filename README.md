# 🕋 Hajj Data Chatbot

An enhanced multilingual chatbot for exploring Hajj company data with natural language queries.

## Features

- 🌍 **Multilingual Support**: Seamlessly handles Arabic and English queries
- 🎨 **Modern UI**: Beautiful, responsive design with custom styling
- 📊 **Data Visualization**: Interactive tables and statistics
- 💾 **Export Functionality**: Download query results as CSV
- 🔍 **Transparent Queries**: View the generated SQL for each query
- 💡 **Example Questions**: Quick-start templates in both languages
- 📈 **Database Statistics**: Real-time insights about your data

## Setup

1. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Create a `.streamlit/secrets.toml` file with your OpenAI API key:
\`\`\`toml
key = "your-openai-api-key"
\`\`\`

3. Ensure your `hajj_companies.db` SQLite database is in the same directory

4. Run the app:
\`\`\`bash
streamlit run app.py
\`\`\`

## Database Schema

The app expects a table named `agencies` with the following columns:
- `hajj_company_ar`: Arabic company name
- `hajj_company_en`: English company name
- `city`: City location
- `country`: Country location
- `email`: Contact email
- `is_authorized`: Authorization status (1 or 0)

## Usage

Simply type your question in natural language (Arabic or English) and the chatbot will:
1. Convert your question to SQL
2. Query the database
3. Present results in a natural, conversational format
4. Display data in an interactive table
5. Allow you to download results

## Example Questions

- "Show me all authorized Hajj companies"
- "List companies in Saudi Arabia"
- "How many agencies are in each country?"
- "أظهر لي الشركات المعتمدة"
- "ما هي الشركات في مكة؟"
