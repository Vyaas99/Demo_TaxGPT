import streamlit as st
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, auth
from pdfminer.high_level import extract_text
from io import BytesIO  # For handling uploaded file content

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

def extract_text_from_files(files):
    """Extract text from uploaded PDF files."""
    extracted_text = ""
    for file in files:
        try:
            file_content = file.read()
            text = extract_text(BytesIO(file_content))  # Extract text from PDF
            extracted_text += text + "\n"
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")
    return extracted_text

def login_user(email, password):
    """Authenticate a user using Firebase."""
    try:
        user = auth.get_user_by_email(email)
        st.session_state["user"] = user
        st.success(f"Logged in as {user.email}")
        return user
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def signup_user(email, password):
    """Create a new user using Firebase."""
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

    # Initialize session state for user, messages, and context
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "context" not in st.session_state:
        st.session_state.context = ""

    # Sidebar for login or sign-up
    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if not st.session_state["user"]:
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
    if st.session_state["user"]:
        st.sidebar.title("User Preferences")
        preferred_region = st.sidebar.selectbox("Select Your Tax Region", ["United States", "Canada", "United Kingdom", "Other"])
        preferred_language = st.sidebar.selectbox("Select Language", ["English", "French", "Spanish", "German", "Other"])
        
        # File Upload Section
        st.sidebar.header("Upload Tax Files")
        uploaded_files = st.sidebar.file_uploader("Upload your tax-related documents (PDF only):", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            # Extract and store context from uploaded files
            context = extract_text_from_files(uploaded_files)
            st.session_state.context = context
            st.sidebar.success("Context extracted and saved!")

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("Ask your tax-related question:"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Display user message in chat container
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate assistant response with OpenAI API
            with st.chat_message("assistant"):
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are TaxGPT, an AI specialized in providing clear, accurate, and professional guidance on tax-related matters. "
                            "Your expertise spans multiple regions, including the United States, Canada, the United Kingdom, and other jurisdictions. "
                            "You are trained to: \n"
                            "1. Explain complex tax concepts in simple, user-friendly language. \n"
                            "2. Provide region-specific advice while clarifying general principles when exact legal advice is beyond your scope. \n"
                            "3. Leverage uploaded user documents to extract relevant context and provide personalized answers. \n"
                            "4. Avoid offering legal or financial advice where professional certification is required and instead guide users to consult a certified tax professional. \n\n"
                            "Your responses should be concise, relevant, and professional, while maintaining an approachable tone. "
                            "Use examples where helpful and ensure clarity in every explanation."
                        )
                    },
                    {
                        "role": "system",
                        "content": f"You should provide responses specific to the tax region '{preferred_region or 'United States'}' "
                                   f"and in the language '{preferred_language or 'English'}'."
                    },
                    {
                        "role": "system",
                        "content": f"Here is additional context from the uploaded files: {st.session_state.context}"
                    }
                ] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]


                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    stream=True,
                )
                response = ""
                for chunk in stream:
                    # Collect streamed content coherently
                    content = chunk.choices[0].delta.content or ""
                    response += content

                # Display the full response once it's complete
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

        # Footer
        st.markdown("---")
        st.caption("Powered by Tax GPT | An AI-driven tax assistant")

if __name__ == "__main__":
    main()
