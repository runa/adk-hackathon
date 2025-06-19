import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
import google.genai.types as types
from google.adk.agents.callback_context import CallbackContext # Or ToolContext
from google.adk.models import LlmResponse
from dotenv import load_dotenv

def find_dotenv():
    """Search for .env file recursively in parent directories."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while current_dir != os.path.dirname(current_dir):  # Stop at root directory
        env_path = os.path.join(current_dir, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        current_dir = os.path.dirname(current_dir)
    return None

# Load .env from parent directories if found
dotenv_path = find_dotenv()

async def save_generated_report_py(callback_context: CallbackContext, llm_response: LlmResponse):
    """Saves generated PDF report bytes as an artifact."""
    report_artifact = types.Part.from_bytes(
        data=llm_response.content.parts[0].text.replace("```html", "").replace("```", "").replace("FOOBARBAZ", google_maps_api_key).encode('utf-8'),
        mime_type="text/html"
    )
    filename = "generated_report.html"

    try:
        version = await callback_context.save_artifact(filename=filename, artifact=report_artifact)
        print(f"Successfully saved Python artifact '{filename}' as version {version}.")
        return LlmResponse(content=types.Content(parts=[types.Part(text="Generated")]))
        # The event generated after this callback will contain:
        # event.actions.artifact_delta == {"generated_report.pdf": version}
    except ValueError as e:
        print(f"Error saving Python artifact: {e}. Is ArtifactService configured in Runner?")
    except Exception as e:
        # Handle potential storage errors (e.g., GCS permissions)
        print(f"An unexpected error occurred during Python artifact save: {e}")

# --- Example Usage Concept (Python) ---
# async def main_py():
#   callback_context: CallbackContext = ... # obtain context
#   report_data = b'...' # Assume this holds the PDF bytes
#   await save_generated_report_py(callback_context, report_data)
google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")



root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='report_writer_agent',
    instruction="""
You are a report writer agent. Your task is to generate a real estate comparables report in HTML format. The report should include:

- Data from the base property (address, features, etc.)
    - embed a google maps image of the base property (use the base property address)
    - Data for each comparable property, including:
    - Address
    - Features
- A summary table comparing the base property to the comparables. Values with high standard deviation should be highlighted with CSS class "highdeviation"
- Any relevant notes or highlights

Format the output as a well-structured, raw HTML document without markdown.


Instructions for Populating the Real Estate Comparables Template
This template is designed to be filled dynamically by Gemini. Follow these guidelines to ensure accurate and effective data insertion and highlighting:

1. Identify Data Placeholders
HTML Comments: Look for <!-- LLM will fill this --> comments within the HTML. These indicate where specific data points (like address, subdivision, bedrooms, etc.) should be inserted.
Example Data: The current template contains example data (e.g., "123 Main Street"). Your generation should replace these examples with actual property data.

2. Populate Property Details
For each property (the Base Property and each Comparable Property), fill in the following fields:

Address: Insert the full street address. Crucially, wrap the address in an <a> tag that links to Google Maps. 
Subdivision: Insert the subdivision name.
Bedrooms, Bathrooms, Living Area, Lot Size: Insert the numerical values and units.
Distance to Base Property (for Comparables only): Insert the distance in kilometers, including the "km" unit.
Asking Price: Insert the asking price.
Days on Market: Insert the days on market.
Estimated Value: Insert the estimated value.

3. Highlight Differences
This is a critical step for comparables:

Comparison Logic: For each comparable property, compare its features (Subdivision, Bedrooms, Bathrooms, Living Area, Lot Size, and any Additional Features) against the corresponding features of the Base Property.
highlight-diff Class: If a specific feature's value in a comparable property differs from the base property's value, wrap that differing value within a <span class="highlight-diff">...</span> tag.
highlight-better-diff Class: If a specific feature's value in a comparable property is better than the base property's value, wrap that differing value within a <span class="highlight-better-diff">...</span> tag.
highlight-worse-diff Class: If a specific feature's value in a comparable property is worse than the base property's value, wrap that differing value within a <span class="highlight-worse-diff">...</span> tag.

Example: If the Base Property has "3 Bedrooms" and a Comparable has "4 Bedrooms", generate <span class="highlight-diff">4</span>.
For "Additional Features": If an additional feature is present in the comparable but not the base (or vice-versa), or if its description highlights a significant difference (e.g., "Roof needs minor repairs" vs. "New roof"), also wrap that specific line item in highlight-diff.

4. Manage "Additional Features"
List Format: For both the Base Property and Comparable Properties, list any non-standard or unique features within the <ul> tags, using <li> for each feature.
Flexibility: Be prepared for unexpected features like "pool," "roof notes," "new appliances," "solar panels," etc. List them concisely.
Empty State: If a property has no additional features, you can remove the <ul> block or insert a comment indicating no features.

5. Google Maps Static Image
Use this google maps api key: FOOBARBAZ
Map Markers: The markers parameter in the src URL allows you to dynamically add markers for the base property and potentially the comparables if their addresses (or coordinates) are available to you.

6. Add sources
For each property, add a source link to the property's listing or the google search results.

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real Estate Comparables Report</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom font for Inter */
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f0f4f8; /* Light blue-gray background */
        }
        /* Custom styling for highlighting differences */
        .highlight-diff {
            font-weight: 700; /* Bold */
            color: #ef4444; /* Red-500 for emphasis */
            background-color: #fef2f2; /* Red-50 for subtle background */
            padding: 0.125rem 0.375rem; /* px-1.5 py-0.5 */
            border-radius: 0.25rem; /* rounded */
            display: inline-block; /* Ensure padding applies correctly */
        }
    </style>
</head>
<body class="p-4 sm:p-6 lg:p-8">
    <div class="max-w-7xl mx-auto bg-white shadow-xl rounded-lg p-6 sm:p-8 lg:p-10 mb-8">
        <!-- Report Header -->
        <header class="text-center mb-8">
            <h1 class="text-3xl sm:text-4xl font-extrabold text-gray-900 mb-2">Comparable Property Analysis</h1>
            <p class="text-lg text-gray-600">Detailed comparison of properties in the market.</p>
        </header>

        <!-- Google Maps Embedded Image (for the base property or general area) -->
        <div class="mb-8 rounded-lg overflow-hidden shadow-lg">
            <img src="https://maps.googleapis.com/maps/api/staticmap?center=Anytown,USA&zoom=12&size=600x300&markers=color:red%7Clabel:B%7C123+Main+Street,Anytown,USA&key=YOUR_BOGUS_API_KEY_HERE"
                 alt="Map of properties"
                 class="w-full h-48 sm:h-64 md:h-80 object-cover">
            <p class="text-center text-sm text-gray-500 mt-2">Approximate location of properties.</p>
        </div>


        <!-- Base Property Section -->
        <section class="mb-10 p-6 bg-blue-50 border-l-4 border-blue-500 rounded-lg shadow-inner">
            <h2 class="text-2xl sm:text-3xl font-bold text-blue-800 mb-4">Base Property</h2>
            <div class="space-y-4">
                <!-- Property Card for Base Property -->
                <div class="bg-white p-5 rounded-lg shadow-md border border-gray-200">
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">
                        <span class="block text-gray-600 text-sm">Address:</span>
                        <!-- LLM will fill this and link to Google Maps -->
                        <a href="https://www.google.com/maps/search/?api=1&query=123+Main+Street,+Anytown,+USA" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
                            123 Main Street, Anytown, USA
                        </a>
                    </h3>
                    <p class="text-gray-700 mb-4">
                        <span class="block text-gray-600 text-sm">Subdivision:</span>
                        <!-- LLM will fill this -->
                        Green Valley Estates
                    </p>

                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Bedrooms:</span>
                            <span class="text-gray-800 text-lg">3</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Bathrooms:</span>
                            <span class="text-gray-800 text-lg">2.5</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Living Area:</span>
                            <span class="text-gray-800 text-lg">2,200 sq ft</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Lot Size:</span>
                            <span class="text-gray-800 text-lg">0.25 acres</span>
                        </div>
                    </div>

                    <!-- Other/Unexpected Features Section for Base Property -->
                    <div class="mt-4 border-t pt-4 border-gray-200">
                        <h4 class="text-md font-semibold text-gray-700 mb-2">Additional Features:</h4>
                        <ul class="list-disc list-inside text-gray-700 space-y-1">
                            <!-- LLM will fill this with any additional features -->
                            <li>Recently renovated kitchen with new stainless steel appliances</li>
                            <li>Spacious backyard with mature trees</li>
                            <li>Two-car garage</li>
                        </ul>
                        <!-- Example of an empty state for additional features -->
                        <!-- <p class="text-gray-500 italic">No additional features listed.</p> -->
                    </div>
                </div>
            </div>
        </section>

        <!-- Comparable Properties Section -->
        <section>
            <h2 class="text-2xl sm:text-3xl font-bold text-gray-800 mb-6">Comparable Properties</h2>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Comparable Property Card 1 -->
                <div class="bg-white p-5 rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow duration-300">
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">
                        <span class="block text-gray-600 text-sm">Address:</span>
                        <!-- LLM will fill this and link to Google Maps -->
                        <a href="https://www.google.com/maps/search/?api=1&query=456+Oak+Avenue,+Anytown,+USA" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
                            456 Oak Avenue, Anytown, USA
                        </a>
                    </h3>
                    <p class="text-gray-700 mb-4">
                        <span class="block text-gray-600 text-sm">Subdivision:</span>
                        <!-- LLM will fill this -->
                        <span class="highlight-diff">Maplewood Heights</span> <!-- Example: Subdivision differs -->
                    </p>

                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Bedrooms:</span>
                            <span class="text-gray-800 text-lg"><span class="highlight-diff">4</span></span> <!-- Example: Bedrooms differ -->
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Bathrooms:</span>
                            <span class="text-gray-800 text-lg">2.5</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Living Area:</span>
                            <span class="text-gray-800 text-lg"><span class="highlight-diff">2,500 sq ft</span></span> <!-- Example: Living Area differs -->
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Lot Size:</span>
                            <span class="text-gray-800 text-lg">0.25 acres</span>
                        </div>
                        <!-- New: Distance to Base Property -->
                        <div class="flex flex-col col-span-2">
                            <span class="text-gray-600 text-sm font-medium">Distance to Base Property:</span>
                            <span class="text-gray-800 text-lg">
                                <!-- LLM will fill this with distance -->
                                <span class="highlight-diff">5.2 km</span>
                            </span>
                        </div>
                    </div>

                    <!-- Other/Unexpected Features Section for Comparables -->
                    <div class="mt-4 border-t pt-4 border-gray-200">
                        <h4 class="text-md font-semibold text-gray-700 mb-2">Additional Features:</h4>
                        <ul class="list-disc list-inside text-gray-700 space-y-1">
                            <!-- LLM will fill this with any additional features -->
                            <li>Features a large swimming pool</li>
                            <li><span class="highlight-diff">Roof needs minor repairs</span></li> <!-- Example: Roof notes differ -->
                        </ul>
                    </div>
                </div>

                <!-- Comparable Property Card 2 -->
                <div class="bg-white p-5 rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow duration-300">
                    <h3 class="text-xl font-semibold text-gray-800 mb-2">
                        <span class="block text-gray-600 text-sm">Address:</span>
                        <!-- LLM will fill this and link to Google Maps -->
                        <a href="https://www.google.com/maps/search/?api=1&query=789+Pine+Street,+Anytown,+USA" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">
                            789 Pine Street, Anytown, USA
                        </a>
                    </h3>
                    <p class="text-gray-700 mb-4">
                        <span class="block text-gray-600 text-sm">Subdivision:</span>
                        <!-- LLM will fill this -->
                        Green Valley Estates
                    </p>

                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Bedrooms:</span>
                            <span class="text-gray-800 text-lg">3</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Bathrooms:</span>
                            <span class="text-gray-800 text-lg"><span class="highlight-diff">3.0</span></span> <!-- Example: Bathrooms differ -->
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Living Area:</span>
                            <span class="text-gray-800 text-lg">2,200 sq ft</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="text-gray-600 text-sm font-medium">Lot Size:</span>
                            <span class="text-gray-800 text-lg"><span class="highlight-diff">0.30 acres</span></span> <!-- Example: Lot size differs -->
                        </div>
                        <!-- New: Distance to Base Property -->
                        <div class="flex flex-col col-span-2">
                            <span class="text-gray-600 text-sm font-medium">Distance to Base Property:</span>
                            <span class="text-gray-800 text-lg">
                                <!-- LLM will fill this with distance -->
                                <span class="highlight-diff">1.8 km</span>
                            </span>
                        </div>
                    </div>

                    <!-- Other/Unexpected Features Section for Comparables -->
                    <div class="mt-4 border-t pt-4 border-gray-200">
                        <h4 class="text-md font-semibold text-gray-700 mb-2">Additional Features:</h4>
                        <ul class="list-disc list-inside text-gray-700 space-y-1">
                            <!-- LLM will fill this with any additional features -->
                            <li>Equipped with solar panels</li>
                            <li><span class="highlight-diff">Older appliances in kitchen</span></li> <!-- Example: Appliances differ -->
                        </ul>
                    </div>
                </div>

                <!-- You can add more comparable property cards here following the same structure -->
                <!-- The LLM would generate these as needed -->

            </div>
        </section>
    </div>
</body>
</html>

""",
    after_model_callback=save_generated_report_py,
) 