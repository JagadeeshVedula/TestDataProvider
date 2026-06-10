import pandas as pd
from faker import Faker

class DataEngine:
    def __init__(self):
        self.fake = Faker()
        # Mapping clean UI names to actual Faker provider methods
        self.providers = {
            "First Name": self.fake.first_name,
            "Last Name": self.fake.last_name,
            "Full Name": self.fake.name,
            "Email Address": self.fake.email,
            "Phone Number": self.fake.phone_number,
            "Company Name": self.fake.company,
            "Job Title": self.fake.job,
            "Street Address": self.fake.street_address,
            "City": self.fake.city,  # depends on address provider
            "State": self.fake.state,  # depends on address provider
            "Country": self.fake.country, # depends on address provider
            "UUID": self.fake.uuid4,
            "Date (Recent)": lambda: self.fake.date_this_decade().strftime("%Y-%m-%d"),
            "Future Date": lambda: self.fake.date_this_century(before_today=False, after_today=True).strftime("%Y-%m-%d"),
            "Integer (10-1000)": lambda: self.fake.random_int(min=10, max=1000),
            "DOB(Age 18-80)": lambda: self.fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%d-%m-%Y"),
        }

    def get_available_features(self):
        return list(self.providers.keys())

    def generate(self, schema, num_rows):
        """
        schema: list of dicts, e.g., [{"col_name": "Email", "type": "Email Address"}]
        """
        data = []
        for _ in range(num_rows):
            row = {}
            
            # Generate consistent address data if any geographic fields are in the schema
            # Use a single English locale so country -> state -> city -> street address flow is consistent.
            address_fields = [
                f
                for f in schema
                if f["type"] in ["City", "State", "Country", "Street Address"]
            ]
            consistent_address = None
            if address_fields:
                consistent_address = self._generate_consistent_address_data()
            
            # First pass: generate all non-email fields to have names available for email generation
            for field in schema:
                col_name = field["col_name"]
                provider_type = field["type"]
                
                # Skip email for now, will handle in second pass
                if provider_type == "Email Address":
                    continue
                
                # Use consistent address data for geographic fields
                if provider_type == "City" and consistent_address:
                    row[col_name] = consistent_address['city']
                elif provider_type == "State" and consistent_address:
                    row[col_name] = consistent_address['state']
                elif provider_type == "Country" and consistent_address:
                    row[col_name] = consistent_address['country']
                elif provider_type == "Street Address" and consistent_address:
                    row[col_name] = consistent_address['street_address']
                else:
                    # Fetch provider method, default to standard text if missing
                    provider_method = self.providers.get(provider_type, self.fake.word)
                    row[col_name] = provider_method()
            
            # Second pass: handle email generation with name awareness
            for field in schema:
                col_name = field["col_name"]
                provider_type = field["type"]
                
                if provider_type == "Email Address":
                    # Try to find name fields already generated
                    email = self._generate_email_from_names(row, schema)
                    row[col_name] = email
            
            data.append(row)
            
        return pd.DataFrame(data)
    
    def _generate_consistent_address_data(self):
        """Generate country, state, city, and street address from the same English locale."""
        from faker import Faker
        
        # Map a supported English locale to a fixed country name.
        locale_country_map = {
            'en_US': 'United States',
            'en_CA': 'Canada',
            'en_AU': 'Australia',
            'en_IN': 'India',
            'en_NZ': 'New Zealand',
        }
        selected_locale = self.fake.random_element(list(locale_country_map.keys()))
        try:
            fake_locale = Faker(selected_locale)
        except Exception:
            fake_locale = self.fake
            selected_locale = 'en_US'
        
        country = locale_country_map.get(selected_locale, 'United States')
        state = fake_locale.state() if hasattr(fake_locale, 'state') else ''
        if not state:
            state = self._fallback_state_for_locale(selected_locale)

        city = self._city_for_state(selected_locale, state)
        if not city:
            city = fake_locale.city()

        street_address = (
            fake_locale.street_address()
            if hasattr(fake_locale, 'street_address')
            else fake_locale.address()
        )
        
        return {
            'country': country,
            'state': state,
            'city': city,
            'street_address': street_address,
        }

    def _fallback_state_for_locale(self, locale_code):
        states = {
            'en_US': [
                'California', 'Texas', 'New York', 'Florida', 'Illinois',
                'Pennsylvania', 'Ohio', 'Georgia', 'North Carolina', 'Michigan',
            ],
            'en_CA': [
                'Ontario', 'Quebec', 'British Columbia', 'Alberta', 
                'Manitoba', 'Saskatchewan', 'Nova Scotia', 'New Brunswick',
                'Newfoundland and Labrador', 'Prince Edward Island',
            ],
            'en_AU': [
                'New South Wales', 'Victoria', 'Queensland', 'Western Australia',
                'South Australia', 'Tasmania', 'Northern Territory',
                'Australian Capital Territory',
            ],
            'en_IN': [
                'Maharashtra', 'Karnataka', 'Tamil Nadu', 'West Bengal',
                'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'Telangana',
                'Madhya Pradesh', 'Kerala',
            ],
            'en_NZ': [
                'Auckland', 'Wellington', 'Canterbury', 'Otago',
                'Waikato', 'Bay of Plenty', 'Manawatu-Wanganui',
                'Hawke\'s Bay',
            ],
        }
        locale_states = states.get(locale_code, states['en_US'])
        return self.fake.random_element(locale_states)
    
    def _city_for_state(self, locale_code, state_name):
        state_city_map = {
            'en_US': {
                'California': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento'],
                'Texas': ['Houston', 'Dallas', 'Austin', 'San Antonio'],
                'New York': ['New York', 'Buffalo', 'Rochester', 'Albany'],
                'Florida': ['Miami', 'Orlando', 'Tampa', 'Jacksonville'],
                'Illinois': ['Chicago', 'Springfield', 'Peoria', 'Naperville'],
                'Pennsylvania': ['Philadelphia', 'Pittsburgh', 'Harrisburg', 'Allentown'],
                'Ohio': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo'],
                'Georgia': ['Atlanta', 'Savannah', 'Augusta', 'Macon'],
                'North Carolina': ['Charlotte', 'Raleigh', 'Greensboro', 'Durham'],
                'Michigan': ['Detroit', 'Grand Rapids', 'Lansing', 'Ann Arbor'],
            },
            'en_CA': {
                'Ontario': ['Toronto', 'Ottawa', 'Hamilton', 'London'],
                'Quebec': ['Montreal', 'Quebec City', 'Laval', 'Gatineau'],
                'British Columbia': ['Vancouver', 'Victoria', 'Kelowna', 'Surrey'],
                'Alberta': ['Calgary', 'Edmonton', 'Red Deer', 'Lethbridge'],
                'Manitoba': ['Winnipeg', 'Brandon', 'Steinbach', 'Thompson'],
                'Saskatchewan': ['Regina', 'Saskatoon', 'Prince Albert', 'Moose Jaw'],
                'Nova Scotia': ['Halifax', 'Sydney', 'Truro', 'New Glasgow'],
                'New Brunswick': ['Fredericton', 'Moncton', 'Saint John', 'Bathurst'],
                'Newfoundland and Labrador': ['St. John\'s', 'Corner Brook', 'Gander', 'Grand Falls'],
                'Prince Edward Island': ['Charlottetown', 'Summerside', 'Cornwall', 'Montague'],
            },
            'en_AU': {
                'New South Wales': ['Sydney', 'Newcastle', 'Wollongong', 'Albury'],
                'Victoria': ['Melbourne', 'Geelong', 'Ballarat', 'Bendigo'],
                'Queensland': ['Brisbane', 'Cairns', 'Gold Coast', 'Townsville'],
                'Western Australia': ['Perth', 'Fremantle', 'Bunbury', 'Geraldton'],
                'South Australia': ['Adelaide', 'Mount Gambier', 'Murray Bridge', 'Whyalla'],
                'Tasmania': ['Hobart', 'Launceston', 'Devonport', 'Burnie'],
                'Northern Territory': ['Darwin', 'Alice Springs', 'Katherine', 'Tennant Creek'],
                'Australian Capital Territory': ['Canberra'],
            },
            'en_IN': {
                'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik'],
                'Karnataka': ['Bengaluru', 'Mysore', 'Mangalore', 'Hubli'],
                'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli'],
                'West Bengal': ['Kolkata', 'Howrah', 'Durgapur', 'Siliguri'],
                'Gujarat': ['Ahmedabad', 'Vadodara', 'Surat', 'Rajkot'],
                'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota'],
                'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Varanasi', 'Agra'],
                'Telangana': ['Hyderabad', 'Warangal', 'Nizamabad', 'Khammam'],
                'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur'],
                'Kerala': ['Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Kollam'],
            },
            'en_NZ': {
                'Auckland': ['Auckland', 'Manukau', 'North Shore', 'Waitakere'],
                'Wellington': ['Wellington', 'Lower Hutt', 'Upper Hutt', 'Porirua'],
                'Canterbury': ['Christchurch', 'Timaru', 'Ashburton', 'Kaiapoi'],
                'Otago': ['Dunedin', 'Invercargill', 'Queenstown', 'Wanaka'],
                'Waikato': ['Hamilton', 'Cambridge', 'Te Awamutu', 'Taupo'],
                'Bay of Plenty': ['Tauranga', 'Rotorua', 'Whakatane', 'Opotiki'],
                'Manawatu-Wanganui': ['Palmerston North', 'Whanganui', 'Masterton', 'Feilding'],
                'Hawke\'s Bay': ['Napier', 'Hastings', 'Waipukurau', 'Waipawa'],
            },
        }
        cities = state_city_map.get(locale_code, {}).get(state_name)
        if cities:
            return self.fake.random_element(cities)
        return ''
    
    def _generate_email_from_names(self, row, schema):
        """Generate email based on available name fields, otherwise random email"""
        # Get the column names for each field type
        full_name_col = None
        first_name_col = None
        last_name_col = None
        
        for field in schema:
            if field["type"] == "Full Name":
                full_name_col = field["col_name"]
            elif field["type"] == "First Name":
                first_name_col = field["col_name"]
            elif field["type"] == "Last Name":
                last_name_col = field["col_name"]
        
        # Generate email based on available names
        if full_name_col and full_name_col in row:
            # Use full name: remove spaces and use as base
            name_base = row[full_name_col].replace(" ", ".").lower()
            domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'example.com', 'mail.com']
            domain = self.fake.random_element(domains)
            return f"{name_base}@{domain}"
        
        elif first_name_col and first_name_col in row and last_name_col and last_name_col in row:
            # Use first and last name
            first_name = row[first_name_col].lower()
            last_name = row[last_name_col].lower()
            domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'example.com', 'mail.com']
            domain = self.fake.random_element(domains)
            # Generate with different formats
            format_choice = self.fake.random_int(min=0, max=2)
            if format_choice == 0:
                return f"{first_name}.{last_name}@{domain}"
            elif format_choice == 1:
                return f"{first_name}_{last_name}@{domain}"
            else:
                return f"{first_name}{last_name}@{domain}"
        
        elif first_name_col and first_name_col in row:
            # Use only first name
            first_name = row[first_name_col].lower()
            domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'example.com', 'mail.com']
            domain = self.fake.random_element(domains)
            return f"{first_name}@{domain}"
        
        else:
            # Fallback to random email if no names available
            return self.fake.email()