import os
import asyncio
import sys
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from googleapiclient.discovery import build
from playwright.async_api import Page
from urllib.parse import urlparse, parse_qs

# Fix for Windows asyncio subprocess issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load environment variables from the .env file in the synapse-agent directory
# Try multiple possible locations to ensure it works
env_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),  # ../synapse-agent/.env
    os.path.join(os.path.dirname(__file__), '..', '.env'),  # synapse-agent/.env
    '.env'  # current directory
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

# This is the path where Playwright will store the browser session data.
# It's crucial for persistent authentication.
USER_DATA_DIR = "./playwright_user_data"

# Create screenshots directory if it doesn't exist
SCREENSHOTS_DIR = "./screenshots"
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)
    print(f"Created screenshots directory: {SCREENSHOTS_DIR}")

async def search_linkedin_urls(query: str, num_results: int = 10) -> list[str]:
    """
    Performs a Google search using the Google Custom Search API to find LinkedIn profile URLs.
    """
    print("Starting Google Custom Search for LinkedIn profiles...")
    urls = []
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        cse_id = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

        if not api_key or not cse_id:
            print("Error: GOOGLE_API_KEY or CUSTOM_SEARCH_ENGINE_ID not found in environment variables.")
            return []

        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=f"{query} site:linkedin.com/in/", cx=cse_id, num=num_results).execute()
        
        if 'items' in res:
            for item in res['items']:
                urls.append(item['link'])
        
        print(f"Found {len(urls)} potential profile URLs.")
        return urls

    except requests.exceptions.ConnectionError as e:
        print(f"Network Error: Could not connect to Google's servers. This is likely a local network issue (firewall, proxy, DNS). Details: {e}")
        return []
    except Exception as e:
        # Catching potential googleapiclient errors specifically if possible
        if "NameResolutionError" in str(e) or "gaierror" in str(e):
             print(f"Network Error: DNS resolution failed for Google's servers. Check your internet connection and DNS settings. Details: {e}")
        else:
            print(f"An unexpected error occurred during the Google Custom Search: {e}")
        return []

class LinkedInParser:
    """
    This class now uses Playwright's Async API for non-blocking browser automation,
    making it compatible with FastAPI.
    """
    def __init__(self, page: Page):
        self.page = page

    async def scrape_profile(self, profile_url: str):
        """
        This method is updated to use Playwright's Async API with more robust selectors.
        """
        try:
            print(f"Navigating to: {profile_url}")
            await self.page.goto(profile_url, wait_until='domcontentloaded')
            
            # Check if we're redirected to auth wall
            current_url = self.page.url
            if "authwall" in current_url or "login" in current_url:
                print(f"Hit LinkedIn auth wall, current URL: {current_url}")
                return {
                    "error": "LinkedIn authentication required - hit auth wall",
                    "name": "N/A",
                    "headline": "N/A",
                    "experience": [],
                    "education": []
                }
            
            # Try multiple possible selectors for LinkedIn's main content
            main_selectors = [
                ".scaffold-layout__main",
                ".application-outlet", 
                "main",
                ".profile",
                "[data-section='profile']",
                "body"
            ]
            
            main_content_found = False
            for selector in main_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    main_content_found = True
                    print(f"Found main content with selector: {selector}")
                    break
                except:
                    continue
            
            if not main_content_found:
                print(f"Warning: Could not find main content selectors, proceeding anyway...")
            
            # Wait a bit more for dynamic content to load
            await asyncio.sleep(3)
            
            # Take a screenshot for debugging (optional)
            try:
                await self.page.screenshot(path=f"debug_screenshot_{profile_url.split('/')[-1]}.png")
                print(f"Debug screenshot saved for {profile_url}")
            except Exception as e:
                print(f"Could not save screenshot: {e}")

            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Debug: Print page title to verify we're on the right page
            page_title = await self.page.title()
            print(f"Page title: {page_title}")

            # Try multiple possible selectors for name
            name = "N/A"
            name_selectors = [
                'h1.text-heading-xlarge',
                'h1[data-test="profile-title"]',
                '.profile-info__name',
                '.top-card-layout__title',
                'h1.top-card-layout__title',
                '.pv-text-details__title',
                'h1',  # Generic h1 as fallback
                '.artdeco-entity-lockup__title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.get_text(strip=True):
                    name = name_elem.get_text(strip=True)
                    print(f"Found name '{name}' with selector: {selector}")
                    break
            
            if name == "N/A":
                print("Could not find candidate name with any selector")
                # Debug: Print some of the page content to see what we're working with
                h1_tags = soup.find_all('h1')
                print(f"Found {len(h1_tags)} h1 tags on page")
                for i, h1 in enumerate(h1_tags[:3]):  # Print first 3 h1 tags
                    print(f"H1 {i+1}: {h1.get_text(strip=True)[:100]}")  # First 100 chars
            
            # Try multiple possible selectors for headline/title
            headline = "N/A"
            headline_selectors = [
                'div.text-body-medium',
                '.top-card-layout__headline',
                '.pv-text-details__title-text',
                '.profile-info__headline',
                '.text-body-medium.break-words',
                '[data-generated-suggestion-target]'
            ]
            
            for selector in headline_selectors:
                headline_elem = soup.select_one(selector)
                if headline_elem and headline_elem.get_text(strip=True):
                    headline = headline_elem.get_text(strip=True)
                    print(f"Found headline '{headline}' with selector: {selector}")
                    break
            
            profile_data = {
                "name": name,
                "headline": headline,
                "experience": [],
                "education": []
            }

            # Modern LinkedIn Experience Section - Updated selectors
            print("Looking for experience section...")
            
            # Try multiple approaches to find experience
            experience_found = False
            
            # Approach 1: Look for modern LinkedIn experience structure
            experience_sections = soup.find_all('section', {'id': lambda x: x and 'experience' in x.lower()})
            if not experience_sections:
                # Look for sections containing "Experience" text
                all_sections = soup.find_all('section')
                for section in all_sections:
                    if section.get_text() and 'Experience' in section.get_text():
                        experience_sections.append(section)
            
            print(f"Found {len(experience_sections)} potential experience sections")
            
            for section in experience_sections:
                # Look for modern LinkedIn list items
                experience_items = section.find_all(['li', 'div'], class_=lambda x: x and any(
                    cls in str(x).lower() for cls in ['pvs-entity', 'experience-item', 'entity-result', 'profile-section-card']))
                
                print(f"Found {len(experience_items)} potential experience items in section")
                
                for item in experience_items[:5]:  # Limit to first 5 experiences
                    try:
                        # Get all text content and try to parse it
                        full_text = item.get_text(separator='|', strip=True)
                        lines = [line.strip() for line in full_text.split('|') if line.strip()]
                        
                        # Look for job title (usually first non-empty line or with role keywords)
                        title = "N/A"
                        company = "N/A" 
                        duration = "N/A"
                        
                        for i, line in enumerate(lines):
                            # Title is usually first or contains job keywords
                            if i == 0 or any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'analyst', 'director', 'ceo', 'founder', 'lead']):
                                if title == "N/A":
                                    title = line
                            # Company is often after title or contains company indicators
                            elif any(keyword in line.lower() for keyword in ['inc', 'corp', 'company', 'ltd', 'llc']) or (i == 1 and company == "N/A"):
                                company = line
                            # Duration contains time indicators
                            elif any(keyword in line.lower() for keyword in ['year', 'month', 'present', '2020', '2021', '2022', '2023', '2024', '2025']) and duration == "N/A":
                                duration = line
                        
                        # Alternative: Look for specific elements with better selectors
                        if title == "N/A":
                            title_elem = item.find(['span', 'div', 'a'], class_=lambda x: x and any(
                                cls in str(x).lower() for cls in ['entity-result__title', 't-16', 't-bold', 'profile-section-card__title']))
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                        
                        if company == "N/A":
                            company_elem = item.find(['span', 'div'], class_=lambda x: x and any(
                                cls in str(x).lower() for cls in ['entity-result__subtitle', 't-14', 'profile-section-card__subtitle']))
                            if company_elem:
                                company = company_elem.get_text(strip=True)
                        
                        # Only add if we found meaningful data
                        if title != "N/A" and len(title) > 2:
                            profile_data["experience"].append({
                                "title": title,
                                "company": company,
                                "duration": duration
                            })
                            experience_found = True
                            print(f"Found experience: {title} at {company}")
                    except (AttributeError, TypeError) as e:
                        print(f"Error parsing experience item: {e}")
                        continue
            
            # Approach 2: If no structured experience found, look for any job-related content
            if not experience_found:
                print("No structured experience found, trying alternative approach...")
                all_text_divs = soup.find_all('div', class_=lambda x: x and 'pvs-entity' in str(x).lower())
                
                for div in all_text_divs[:10]:  # Check first 10 divs
                    text_content = div.get_text(strip=True)
                    # Look for job-related keywords
                    if any(keyword in text_content.lower() for keyword in [
                        'engineer', 'developer', 'manager', 'analyst', 'director', 'ceo', 'founder', 'lead',
                        'software', 'python', 'machine learning', 'full-time', 'part-time'
                    ]):
                        lines = [line.strip() for line in text_content.replace('\n', '|').split('|') if line.strip()]
                        if len(lines) >= 1:
                            profile_data["experience"].append({
                                "title": lines[0],
                                "company": lines[1] if len(lines) > 1 else "N/A",
                                "duration": lines[2] if len(lines) > 2 else "N/A"
                            })
                            experience_found = True
                            print(f"Found alternative experience: {lines[0]}")

            print(f"Found {len(profile_data['experience'])} experience entries")

            # Modern LinkedIn Education Section - Updated selectors
            print("Looking for education section...")
            
            education_found = False
            
            # Approach 1: Look for modern LinkedIn education structure
            education_sections = soup.find_all('section', {'id': lambda x: x and 'education' in x.lower()})
            if not education_sections:
                # Look for sections containing "Education" text
                all_sections = soup.find_all('section')
                for section in all_sections:
                    if section.get_text() and 'Education' in section.get_text():
                        education_sections.append(section)
            
            print(f"Found {len(education_sections)} potential education sections")
            
            for section in education_sections:
                # Look for modern LinkedIn list items
                education_items = section.find_all(['li', 'div'], class_=lambda x: x and any(
                    cls in str(x).lower() for cls in ['pvs-entity', 'education-item', 'entity-result', 'profile-section-card']))
                
                print(f"Found {len(education_items)} potential education items in section")
                
                for item in education_items[:3]:  # Limit to first 3 education entries
                    try:
                        # Get all text content and try to parse it
                        full_text = item.get_text(separator='|', strip=True)
                        lines = [line.strip() for line in full_text.split('|') if line.strip()]
                        
                        # Look for school name and degree
                        school = "N/A"
                        degree = "N/A"
                        duration = "N/A"
                        
                        for i, line in enumerate(lines):
                            # School is usually first or contains university keywords
                            if i == 0 or any(keyword in line.lower() for keyword in ['university', 'college', 'institute', 'school']):
                                if school == "N/A":
                                    school = line
                            # Degree contains education keywords
                            elif any(keyword in line.lower() for keyword in ['bachelor', 'master', 'phd', 'degree', 'engineering', 'science', 'arts']) and degree == "N/A":
                                degree = line
                            # Duration contains time indicators
                            elif any(keyword in line.lower() for keyword in ['year', 'month', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']) and duration == "N/A":
                                duration = line
                        
                        # Alternative: Look for specific elements with better selectors
                        if school == "N/A":
                            school_elem = item.find(['span', 'div', 'a'], class_=lambda x: x and any(
                                cls in str(x).lower() for cls in ['entity-result__title', 't-16', 't-bold', 'profile-section-card__title']))
                            if school_elem:
                                school = school_elem.get_text(strip=True)
                        
                        if degree == "N/A":
                            degree_elem = item.find(['span', 'div'], class_=lambda x: x and any(
                                cls in str(x).lower() for cls in ['entity-result__subtitle', 't-14', 'profile-section-card__subtitle']))
                            if degree_elem:
                                degree = degree_elem.get_text(strip=True)
                        
                        # Only add if we found meaningful data
                        if school != "N/A" and len(school) > 2:
                            profile_data["education"].append({
                                "school": school,
                                "degree": degree,
                                "duration": duration
                            })
                            education_found = True
                            print(f"Found education: {degree} from {school}")
                    except (AttributeError, TypeError) as e:
                        print(f"Error parsing education item: {e}")
                        continue
            
            # Approach 2: Look for university/college names anywhere on the page
            if not education_found:
                print("No structured education found, trying alternative approach...")
                # Look for well-known universities and colleges
                university_keywords = [
                    'harvard', 'stanford', 'mit', 'yale', 'princeton', 'caltech', 'columbia', 'upenn', 'dartmouth', 'brown',
                    'cornell', 'duke', 'northwestern', 'johns hopkins', 'chicago', 'berkeley', 'ucla', 'usc', 'nyu',
                    'university', 'college', 'institute', 'school of', 'tech', 'iit', 'bits'
                ]
                
                all_text_divs = soup.find_all('div', class_=lambda x: x and 'pvs-entity' in str(x).lower())
                for div in all_text_divs[:10]:
                    text_content = div.get_text(strip=True)
                    if any(keyword in text_content.lower() for keyword in university_keywords):
                        lines = [line.strip() for line in text_content.replace('\n', '|').split('|') if line.strip()]
                        if len(lines) >= 1:
                            profile_data["education"].append({
                                "school": lines[0],
                                "degree": lines[1] if len(lines) > 1 else "N/A",
                                "duration": lines[2] if len(lines) > 2 else "N/A"
                            })
                            education_found = True
                            print(f"Found alternative education: {lines[0]}")

            print(f"Found {len(profile_data['education'])} education entries")

            return profile_data

        except Exception as e:
            print(f"An error occurred while scraping {profile_url}: {e}")
            # It's good practice to return a more structured error or empty state
            return {
                "error": str(e),
                "name": "N/A",
                "headline": "N/A",
                "experience": [],
                "education": []
            }

    async def send_connection_request(self, profile_url: str, message: str):
        """
        This method is updated to use Playwright's Async API.
        """
        try:
            await self.page.goto(profile_url, wait_until='domcontentloaded')
            
            connect_button = self.page.locator("button:has-text('Invite')").filter(has_text="to connect")
            await connect_button.wait_for(timeout=15000)
            await connect_button.click()

            await self.page.locator("button:has-text('Add a note')").click()
            await self.page.locator("#custom-message").fill(message)
            await self.page.locator("button:has-text('Send now')").click()
            
            print(f"Successfully sent connection request to {profile_url}")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"Failed to send connection request to {profile_url}: {e}")
            try:
                await self.page.locator("button[aria-label='Dismiss']").click()
            except Exception:
                pass
            return False

def llm_call(prompt: str):
    try:
        # Create the client - it automatically picks up GEMINI_API_KEY from environment
        client = genai.Client()
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text

    except Exception as e:
        print(f"An error occurred during the LLM call: {e}")
        # Return a basic JSON structure if everything fails
        return json.dumps({
            "name": "Unknown",
            "linkedin_url": "N/A",
            "fit_score": 0.0,
            "score_breakdown": {
                "education": 0.0,
                "trajectory": 0.0,
                "company": 0.0,
                "skills": 0.0,
                "location": 0.0,
                "tenure": 0.0
            },
            "reasoning": f"Failed to analyze profile due to LLM error: {e}",
            "confidence_score": 0.0,
            "outreach_message": "Unable to generate personalized message"
        })
