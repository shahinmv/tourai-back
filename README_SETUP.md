# TourAI Backend Setup

## Environment Variables Setup

After cloning this repository, you need to set up your environment variables:

1. Copy the `.env` file and add your actual API key:
   ```bash
   # In the .env file, replace 'your_openai_api_key_here' with your actual OpenAI API key
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

2. Install python-dotenv if not already installed:
   ```bash
   pip install python-dotenv
   ```

3. The application will now load your API key from the environment variable instead of having it hardcoded.

## Security Note

- Never commit your `.env` file to git (it's already ignored by .gitignore)
- Never hardcode API keys or secrets in your source code
- Use environment variables for all sensitive configuration

## Running the Application

```bash
python manage.py runserver 0.0.0.0:8001
```

The application should now work with your API key loaded from the environment.