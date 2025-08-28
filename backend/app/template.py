"""
Educational Ebook Template Generator
Based on the reference design with sidebar navigation, structured chapters, and interactive elements.
"""

class EbookTemplate:
    """Template class for generating structured educational ebooks"""
    
    @staticmethod
    def generate_template(title: str, chapters: list, content_data: dict) -> str:
        """Generate a complete markdown ebook following the reference template structure"""
        
        # Generate table of contents for sidebar navigation
        toc_items = []
        for i, chapter in enumerate(chapters, 1):
            toc_items.append(f"- [{i}. {chapter['title']}](#{chapter['title'].lower().replace(' ', '-')})")
            if 'subsections' in chapter:
                for j, subsection in enumerate(chapter['subsections'], 1):
                    toc_items.append(f"  - [{i}.{j} {subsection}](#{subsection.lower().replace(' ', '-')})")
        
        toc = "\n".join(toc_items)
        
        # Main template structure
        template = f"""# {title}
*Interactive ebook*

---

## Table of Contents
{toc}

---

"""
        
        # Generate chapters
        for i, chapter in enumerate(chapters, 1):
            template += f"""## Chapter {i}: {chapter['title']}

{chapter.get('description', '')}

"""
            
            # Generate subsections
            if 'subsections' in chapter:
                for j, subsection in enumerate(chapter['subsections'], 1):
                    template += f"""### {i}.{j} {subsection}

{chapter.get('subsection_content', {}).get(subsection, 'Content for this subsection will be generated based on the source material.')}

"""
                    
                    # Add key points box if specified
                    if 'key_points' in chapter and subsection in chapter['key_points']:
                        points = chapter['key_points'][subsection]
                        template += f"""
> **Key Points:**
> {chr(10).join([f'> - {point}' for point in points])}

"""
                    
                    # Add interactive calculator if specified
                    if 'calculator' in chapter and subsection in chapter['calculator']:
                        calc_data = chapter['calculator'][subsection]
                        template += f"""
#### {calc_data['title']}

**Input Parameters:**
- {calc_data.get('param1', 'Parameter 1')}: ________
- {calc_data.get('param2', 'Parameter 2')}: ________  
- {calc_data.get('param3', 'Parameter 3')}: ________

*[Calculate Results]*

"""
                    
                    # Add specifications table if specified
                    if 'specifications' in chapter and subsection in chapter['specifications']:
                        spec_data = chapter['specifications'][subsection]
                        template += f"""
#### {spec_data.get('title', 'Specifications')}

| {spec_data.get('col1', 'Parameter')} | {spec_data.get('col2', 'Range')} | {spec_data.get('col3', 'Unit')} | {spec_data.get('col4', 'Application')} |
|------|-------|------|------------|
"""
                        for row in spec_data.get('data', []):
                            template += f"| {row.get('param', '')} | {row.get('range', '')} | {row.get('unit', '')} | {row.get('application', '')} |\n"
                        
                        template += "\n"
        
        return template
    
    @staticmethod
    def get_default_structure():
        """Return a default chapter structure based on the reference image"""
        return [
            {
                "title": "Introduction",
                "description": "Overview and fundamental concepts",
                "subsections": [
                    "Basic Properties", 
                    "Manufacturing Process"
                ],
                "key_points": {
                    "Basic Properties": [
                        "Non-pathogenic characteristics",
                        "Viral vector capabilities", 
                        "Gene transfer mechanisms",
                        "Safety profile and applications"
                    ]
                },
                "calculator": {
                    "Manufacturing Process": {
                        "title": "Dose Calculator",
                        "param1": "Sample Volume (μL)",
                        "param2": "Concentration (dose/ml)", 
                        "param3": "Target Dose ($/dose)"
                    }
                },
                "specifications": {
                    "Manufacturing Process": {
                        "title": "Manufacturing Specifications",
                        "col1": "Process",
                        "col2": "Concentration Range",
                        "col3": "Scale",
                        "col4": "Application Method",
                        "data": [
                            {
                                "param": "Small Scale",
                                "range": "10-50L",
                                "unit": "1000-2000L",
                                "application": "Research, Development"
                            },
                            {
                                "param": "Large Scale", 
                                "range": "$100K-500K/dose",
                                "unit": "$10K-50K/dose",
                                "application": "Commercial, Mass Production"
                            }
                        ]
                    }
                }
            },
            {
                "title": "Core Concepts",
                "description": "Detailed exploration of key principles",
                "subsections": [
                    "Mechanism of Action",
                    "Clinical Applications"
                ]
            },
            {
                "title": "Advanced Topics", 
                "description": "In-depth analysis and specialized applications",
                "subsections": [
                    "Quality Control",
                    "Regulatory Considerations"
                ]
            },
            {
                "title": "Practical Applications",
                "description": "Real-world implementations and case studies",
                "subsections": [
                    "Case Studies",
                    "Best Practices"
                ]
            },
            {
                "title": "Assessment and Resources",
                "description": "Learning evaluation and additional materials",
                "subsections": [
                    "Review Questions",
                    "Further Reading"
                ]
            }
        ]