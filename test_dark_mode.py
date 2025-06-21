#!/usr/bin/env python3
"""
Test script to verify dark mode functionality
"""
from app import create_app
from models.tools.user import User
from models.extensions import db

def test_dark_mode():
    app = create_app()
    
    with app.app_context():
        # Get the first user
        user = User.query.first()
        if not user:
            print("No users found in database")
            return
            
        print(f"User: {user.email}")
        print(f"Dark mode preference: {user.dark_mode_preference}")
        
        # Test with client
        with app.test_client() as client:
            # Login as the user
            response = client.post('/auth/login', data={
                'email': user.email,
                'password': 'password'  # Assuming default password
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("Login successful")
                
                # Check the wiki index page
                response = client.get('/wiki/index')
                if response.status_code == 200:
                    html = response.get_data(as_text=True)
                    
                    # Check if dark mode is set in HTML
                    if 'data-theme="dark"' in html:
                        print("✓ Dark mode is correctly set in HTML")
                    elif 'data-theme="light"' in html:
                        print("✗ Light mode is set instead of dark mode")
                    else:
                        print("✗ No theme attribute found in HTML")
                        
                    # Check if CSS variables are present
                    if '--bg-primary: #1a1a1a' in html or '--bg-primary: #1a1a1a;' in html:
                        print("✓ Dark mode CSS variables are present")
                    else:
                        print("✗ Dark mode CSS variables not found")
                        
                    # Check if the search input has proper styling
                    if 'wiki-search-group' in html:
                        print("✓ Wiki search group found in HTML")
                    else:
                        print("✗ Wiki search group not found")
                        
                else:
                    print(f"Failed to get wiki page: {response.status_code}")
            else:
                print("Login failed")

if __name__ == '__main__':
    test_dark_mode() 