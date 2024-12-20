import streamlit as st
import openai

# OpenAI API Key (Replace with your actual key)
openai.api_key = st.secrets["openai"]["api_key"]

def get_ai_response(query, region, language):
    """Fetch AI response from OpenAI API."""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant specializing in tax advice for the {region} region, responding in {language}."},
                {"role": "user", "content": query},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error fetching response: {e}"

def main():
    # App Title
    st.title("Tax GPT: Your Tax Assistant")
    st.subheader("Get real-time tax advice with AI")

    # Sidebar for User Preferences
    st.sidebar.title("User Preferences")
    preferred_region = st.sidebar.selectbox("Select Your Tax Region", ["United States", "Canada", "United Kingdom", "Other"])
    preferred_language = st.sidebar.selectbox("Select Language", ["English", "French", "Spanish", "German", "Other"])
    
    st.sidebar.write(f"Preferred Region: {preferred_region}")
    st.sidebar.write(f"Preferred Language: {preferred_language}")

    # Input Section for Tax Queries
    st.header("Ask Your Tax-Related Question")
    user_query = st.text_area("Enter your question below:", "e.g., What are the tax benefits for small businesses?")

    if st.button("Submit Question"):
        if user_query.strip():
            st.info("Fetching response from AI...")
            ai_response = get_ai_response(user_query, preferred_region, preferred_language)
            st.write(f"**Question:** {user_query}")
            st.success(f"**AI Response:** {ai_response}")
        else:
            st.warning("Please enter a question before submitting.")

    # File Upload Section
    st.header("Upload Tax Files")
    uploaded_files = st.file_uploader("Upload your tax-related documents (e.g., PDFs, spreadsheets, forms):", accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"File Uploaded: {uploaded_file.name}")

    # Footer
    st.markdown("---")
    st.caption("Powered by Tax GPT | An AI-driven tax assistant")

if __name__ == "__main__":
    main()
