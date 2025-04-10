# app.py
import streamlit as st
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import time

# Import the resume parser functions
from main import parse_resume

def main():
    st.set_page_config(page_title="PDF Resume Parser", layout="wide")
    
    st.title("📄PDF Resume Parser - Alpha Testing 1.0.2")
    st.write("Upload one or multiple PDF resumes to extract structured information.")
    
    # File uploader - PDF only, with multiple files allowed
    uploaded_files = st.file_uploader("Choose PDF resume(s)", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        st.write(f"### {len(uploaded_files)} File(s) Uploaded")
        
        # Display file details in a table
        file_details = []
        for file in uploaded_files:
            file_details.append({
                "Filename": file.name,
                "Size (KB)": f"{file.size / 1024:.2f}"
            })
        
        st.table(pd.DataFrame(file_details))
        
        # Check for PDF dependencies
        missing_packages = []
        try:
            import PyPDF2
        except ImportError:
            missing_packages.append("PyPDF2")
        
        try:
            import pdfplumber
        except ImportError:
            missing_packages.append("pdfplumber")
        
        # Show warning if packages are missing
        if missing_packages:
            packages_str = ", ".join(missing_packages)
            st.warning(f"⚠️ Some packages required for PDF parsing are missing: {packages_str}")
            st.info(f"Install with: pip install {' '.join(missing_packages)}")
        
        # Create temporary directory for uploaded files
        temp_dir = tempfile.TemporaryDirectory()
        
        # Parse button
        if st.button("Parse Resumes"):
            # Initialize progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Initialize containers for results
            results_container = st.container()
            combined_data = []
            
            # Process each file
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                progress_bar.progress((i) / len(uploaded_files))
                
                try:
                    # Save the uploaded file to the temp directory
                    file_path = os.path.join(temp_dir.name, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Parse the resume
                    resume_data = parse_resume(file_path)
                    
                    # Add filename to the data
                    resume_data["filename"] = uploaded_file.name
                    
                    # Add to combined data
                    combined_data.append(resume_data)
                    
                    # Small delay to show progress
                    time.sleep(0.5)
                
                except Exception as e:
                    # Add error entry
                    combined_data.append({
                        "filename": uploaded_file.name,
                        "error": str(e),
                        "status": "Failed"
                    })
            
            # Complete the progress bar
            progress_bar.progress(1.0)
            status_text.text(f"Completed processing {len(uploaded_files)} files!")
            
            # Display results
            with results_container:
                st.header("Parsing Results")
                
                # Create tabs for different views
                tabs = st.tabs(["Summary", "Individual Results", "Consolidated Data", "Export"])
                
                # Summary tab
                with tabs[0]:
                    st.subheader("Summary")
                    
                    # Count success/failures
                    success_count = sum(1 for item in combined_data if "error" not in item)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Files", len(uploaded_files))
                    with col2:
                        st.metric("Successfully Parsed", success_count)
                    with col3:
                        st.metric("Failed", len(uploaded_files) - success_count)
                    
                    # Show skills summary if any successful parses
                    if success_count > 0:
                        st.subheader("Common Skills")
                        all_skills = []
                        for data in combined_data:
                            if "Skills" in data and data["Skills"]:
                                all_skills.extend(data["Skills"])
                        
                        # Count occurrences
                        skill_counts = {}
                        for skill in all_skills:
                            if skill in skill_counts:
                                skill_counts[skill] += 1
                            else:
                                skill_counts[skill] = 1
                        
                        # Sort by count
                        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
                        
                        # Display top skills
                        top_skills = sorted_skills[:20]  # Show top 20
                        if top_skills:
                            # Create a DataFrame for the skills
                            skills_df = pd.DataFrame(top_skills, columns=["Skill", "Count"])
                            st.bar_chart(skills_df.set_index("Skill"))
                
                # Individual results tab
                with tabs[1]:
                    st.subheader("Individual Results")
                    
                    for i, data in enumerate(combined_data):
                        with st.expander(f"{i+1}. {data['filename']}"):
                            if "error" in data:
                                st.error(f"Failed to parse: {data['error']}")
                            else:
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.subheader("Personal Information")
                                    if data.get("name"):
                                        st.write(f"**Name:** {data['name']}")
                                    
                                    if data.get("emails"):
                                        st.write("**Email:**")
                                        for email in data["emails"]:
                                            st.write(f"- {email}")
                                    
                                    if data.get("phones"):
                                        st.write("**Phone:**")
                                        for phone in data["phones"]:
                                            st.write(f"- {phone}")
                                
                                with col2:
                                    st.subheader("Social Media")
                                    if data.get("Social Links"):
                                        for platform, links in data["Social Links"].items():
                                            st.write(f"**{platform}:**")
                                            for link in links:
                                                st.write(f"- [{link}]({link})")
                                
                                # Skills section
                                st.subheader("Skills")
                                if data.get("Skills"):
                                    # Display skills as pills
                                    skills_html = ""
                                    for skill in data["Skills"]:
                                        skills_html += f'<span style="background-color: #E6F3FF; color: #0066CC; padding: 5px 10px; margin: 5px; border-radius: 20px; display: inline-block;">{skill}</span>'
                                    
                                    st.markdown(skills_html, unsafe_allow_html=True)
                                else:
                                    st.info("No skills detected")
                
                # Consolidated data tab
                with tabs[2]:
                    st.subheader("Consolidated Data")
                    
                    # Create a consolidated view in a table
                    consolidated = []
                    for data in combined_data:
                        if "error" not in data:
                            consolidated.append({
                                "Filename": data["filename"],
                                "Name": data.get("name", ""),
                                "Email": ", ".join(data.get("emails", [])),
                                "Phone": ", ".join(data.get("phones", [])),
                                "Skills Count": len(data.get("Skills", [])),
                                "Education Count": len(data.get("Education", [])),
                                "Experience Count": len(data.get("Experience", []))
                            })
                    
                    if consolidated:
                        st.dataframe(pd.DataFrame(consolidated))
                    else:
                        st.info("No successfully parsed files to display")
                
                # Export tab
                with tabs[3]:
                    st.subheader("Export Data")
                    
                    # JSON export for all data
                    if combined_data:
                        # Export as JSON
                        json_str = json.dumps(combined_data, indent=2)
                        st.download_button(
                            label="Download All Results (JSON)",
                            data=json_str,
                            file_name="resume_parsing_results.json",
                            mime="application/json"
                        )
                        
                        # Export as CSV (simplified data)
                        if any("error" not in data for data in combined_data):
                            # Create simplified data for CSV
                            csv_data = []
                            for data in combined_data:
                                if "error" not in data:
                                    row = {
                                        "Filename": data["filename"],
                                        "Name": data.get("name", ""),
                                        "Email": "; ".join(data.get("emails", [])),
                                        "Phone": "; ".join(data.get("phones", [])),
                                        "Skills": "; ".join(data.get("Skills", [])),
                                        "LinkedIn": "; ".join(data.get("Social Links", {}).get("LinkedIn", [])),
                                        "GitHub": "; ".join(data.get("Social Links", {}).get("GitHub", []))
                                    }
                                    csv_data.append(row)
                            
                            if csv_data:
                                df = pd.DataFrame(csv_data)
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Download Simplified Results (CSV)",
                                    data=csv,
                                    file_name="resume_parsing_results.csv",
                                    mime="text/csv"
                                )
        
        # Clean up temp files when app reruns
        temp_dir.cleanup()
    
    # Add information about the parser
    with st.sidebar:
        st.header("About")
        st.write("""
        This PDF resume parser extracts structured information from resumes using 
        natural language processing and pattern matching techniques.
        
        **Features:**
        - Multiple PDF upload support
        - Personal information extraction
        - Skills identification
        - Work experience detection
        - Education information extraction
        - Social media links detection
        - Data export in JSON and CSV formats
        
        **Supported File Types:**
        - PDF (.pdf) only
        """)
        
        st.write("---")
        st.write("Developed by Aakkash using Streamlit")

if __name__ == "__main__":
    main()