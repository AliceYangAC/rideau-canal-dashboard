from dashboard import app  # assuming your Dash instance is called app

# Azure looks for a variable named 'app' here
application = app.server
