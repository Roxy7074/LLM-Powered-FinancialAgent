# AI Budget Assistant

Project Overview

The AI Financial Agent is an interactive budgeting assistant built to solve a key problem with personal finance: making actionable decisions based on raw data. Our project moves beyond the static charts and rigid tables of traditional budgeting software to create a conversational tool that provides personalized financial coaching. We designed this application as a sophisticated Retrieval Augmented Generation (RAG) agent combined with a robust data analysis engine.

The core goal is to take a user's spending habits (via CSV upload) and offer actionable, contextual advice that is grounded in both their personal data and objective, real-world financial benchmarks.

Key Features and Technical Approach

1. Retrieval Augmented Generation (RAG) Architecture

The foundation of our project is the RAG architecture, which fulfills the requirement of building a system that goes beyond simple homework assignments by incorporating external data.

Dataset Retrieval: We compiled a public, real-world dataset (benchmarks.csv) using figures from the US Bureau of Labor Statistics (BLS) Consumer Expenditure Survey (2023). This data serves as our external knowledge base.

Contextual Reasoning: When a user asks a question (ex: "How am I doing on rent?"), the Gemini model is 'augmented' with both the user's specific spending and the national average from the BLS dataset. This allows the agent to generate grounded advice, such as confirming that the user is "spending $200 above the national average of $1,300."

2. Logic Engine and Tool Use (Guaranteed Accuracy)

To prevent the mathematical errors common in LLMs, we strictly enforced the "Use Tools" principle. All essential math is performed by our Python Logic Engine (using Pandas), not the LLM.

Accurate Calculations: The engine calculates Monthly Averages (normalizing multi-month data) and determines the precise figures for Needs, Wants, and Savings. This ensures the data presented to the user and the AI is always accurate to two decimal places.

Quantitative Evaluation: The engine runs the 50/30/20 rule analysis, assigning the user a quantifiable "Budget Grade" (A+, C, Needs Work).

3. Interactive Analysis and UX

Conversational Handoff: The application is designed to be seamless. Users can type a question from any page, and the application will automatically switch to the "Gemini Chat Agent" tab, displaying their question and the AI's instant response. This improves user flow dramatically.

Visual Data Analysis: The dashboard provides several visual tools for quantitative analysis:

Spending Trend: A line chart identifying consumption spikes over time (fulfilling the "identify trends" requirement).

Savings Simulator: An interactive tool allowing the user to test the projected savings of cutting "Wants" by varying percentages.

🛠️ Getting Started

Prerequisites

You need Python 3.9+ and Git installed.

Clone the Repository:

git clone [YOUR_REPOSITORY_LINK]
cd ai-budget-agent


Setup Environment and Install Requirements:

# Create virtual environment 
python3 -m venv venv
source venv/bin/activate

# Install all necessary libraries
pip install -r requirements.txt


Generate the RAG Dataset (BLS Benchmarks):
This command runs the script that creates the benchmarks.csv file from real-world data.

python3 fetch_data.py


Add Your API Key:
Create a file named .env in the root directory and paste your Gemini API key inside it:

# .env file content
GOOGLE_API_KEY=AIzaSy...


Run the Application:

streamlit run app.py
