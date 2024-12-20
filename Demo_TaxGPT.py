import streamlit as st
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, auth
import textract  # For extracting text from uploaded files

# OpenAI API Key
client = OpenAI(
  api_key=st.secrets["openai"]["api_key"]
)

# Initialize Firebase Admin SDK using Streamlit Secrets
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(cred)

def get_ai_response(query, region, language, context=""):
    """Fetch AI response from OpenAI API with optional context."""
    try:
        messages = [
            {"role": "system", "content": f"You are a helpful AI assistant specializing in tax advice for the {region} region, responding in {language}."}
        ]
        if context:
            messages.append({"role": "system", "content": f"Here is additional context from the uploaded files: {context}"})
        messages.append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error fetching response: {e}"

def extract_text_from_files(files):
    """Extract text from uploaded files."""
    extracted_text = ""
    for file in files:
        try:
            # Use file.read() to get the file content directly
            content = textract.process(file, input_type='bytes', input_file=file.read())
            extracted_text += content.decode("utf-8") + "\n"
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")
    return extracted_text

def login_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        st.success(f"Logged in as {user.email}")
        return user
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def signup_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        st.success("Account created successfully! Please log in.")
        return user
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def main():
    # App Title
    st.title("Tax GPT: Your Tax Assistant")

    # Sidebar for User Preferences
    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login_user(email, password)

    elif choice == "Sign Up":
        st.subheader("Sign Up")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            signup_user(email, password)

    # Show app functionality if logged in
    if "user" in st.session_state:
        st.sidebar.title("User Preferences")
        preferred_region = st.sidebar.selectbox("Select Your Tax Region", ["United States", "Canada", "United Kingdom", "Other"])
        preferred_language = st.sidebar.selectbox("Select Language", ["English", "French", "Spanish", "German", "Other"])
        
        st.sidebar.write(f"Preferred Region: {preferred_region}")
        st.sidebar.write(f"Preferred Language: {preferred_language}")

        # Input Section for Tax Queries
        st.header("Ask Your Tax-Related Question")
        user_query = st.text_area("Enter your question below:", "e.g., What are the tax benefits for small businesses?")

        # File Upload Section
        st.header("Upload Tax Files")
        uploaded_files = st.file_uploader("Upload your tax-related documents (e.g., PDFs, spreadsheets, forms):", accept_multiple_files=True)
        context = ""
        if uploaded_files:
            context = extract_text_from_files(uploaded_files)
            st.success("Context extracted from files.")

        if st.button("Submit Question"):
            if user_query.strip():
                ai_response = get_ai_response(user_query, preferred_region, preferred_language, context)
                st.write(f"**Question:** {user_query}")
                st.success(f"**AI Response:** {ai_response}")
            else:
                st.warning("Please enter a question before submitting.")

        # Footer
        st.markdown("---")
        st.caption("Powered by Tax GPT | An AI-driven tax assistant")

if __name__ == "__main__":
    main()
