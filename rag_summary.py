# =====================================================
# RAG-BASED RESUME SUMMARY (Lightweight)
# =====================================================

import re
import os
from typing import List, Dict, Tuple

class ResumeRAG:
    def __init__(self):
        self.skill_keywords = [
            'python', 'java', 'javascript', 'react', 'node', 'angular', 'vue',
            'django', 'flask', 'sql', 'mysql', 'mongodb', 'aws', 'docker',
            'git', 'api', 'html', 'css', 'typescript', 'php', 'ruby',
            'c++', 'c#', 'go', 'rust', 'swift', 'kotlin', 'scala'
        ]
        
        self.experience_keywords = [
            'experience', 'years', 'worked', 'developed', 'managed', 'led',
            'created', 'built', 'designed', 'implemented', 'architected'
        ]
        
        self.project_keywords = [
            'project', 'application', 'system', 'platform', 'software',
            'app', 'web app', 'mobile app', 'website', 'tool', 'solution'
        ]
        
        self.education_keywords = [
            'bachelor', 'master', 'degree', 'bsc', 'msc', 'phd',
            'university', 'college', 'institute', 'education'
        ]

    def chunk_resume(self, text: str) -> List[Dict[str, str]]:
        """Chunk resume into meaningful sections"""
        chunks = []
        
        # Split by common resume section patterns
        sections = re.split(r'\n(?=.*?(?:experience|skills|projects|education|summary|objective))', 
                          text.lower(), flags=re.IGNORECASE)
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 20:
                chunks.append({
                    'id': i,
                    'text': section.strip(),
                    'type': self._classify_section(section)
                })
        
        return chunks

    def _classify_section(self, text: str) -> str:
        """Classify section type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in self.skill_keywords):
            return 'skills'
        elif any(word in text_lower for word in self.experience_keywords):
            return 'experience'
        elif any(word in text_lower for word in self.project_keywords):
            return 'projects'
        elif any(word in text_lower for word in self.education_keywords):
            return 'education'
        else:
            return 'general'

    def retrieve_relevant_chunks(self, chunks: List[Dict], query: str) -> List[Dict]:
        """Retrieve relevant chunks based on query"""
        query_lower = query.lower()
        relevant_chunks = []
        
        for chunk in chunks:
            score = 0
            
            # Score based on keyword overlap
            if 'skills' in query_lower and chunk['type'] == 'skills':
                score += 10
            elif 'experience' in query_lower and chunk['type'] == 'experience':
                score += 10
            elif 'projects' in query_lower and chunk['type'] == 'projects':
                score += 10
            
            # Additional scoring based on keyword presence
            if any(word in chunk['text'].lower() for word in self.skill_keywords):
                score += 5
            if any(word in chunk['text'].lower() for word in self.experience_keywords):
                score += 3
            
            if score > 0:
                chunk['relevance_score'] = score
                relevant_chunks.append(chunk)
        
        # Sort by relevance score
        relevant_chunks.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return relevant_chunks[:3]  # Top 3 relevant chunks

    def extract_tech_skills(self, text: str) -> List[str]:
        """Extract technical skills with ratings"""
        skills = []
        
        # Pattern for tech with ratings (stars, dots, percentages, numbers) - preserve original
        patterns = [
            r'(\b(?:python|java|javascript|react|node|angular|vue|django|flask|sql|aws|docker|git|html|css)\b)\s*[:\-]?\s*([⭐★☆●○\d\s]{1,15})',
            r'(\b(?:python|java|javascript|react|node|angular|vue|django|flask|sql|aws|docker|git|html|css)\b)\s*[:\-]?\s*(\d+%|\d+/\d+|\d+\.\d+)',
            r'(\b(?:python|java|javascript|react|node|angular|vue|django|flask|sql|aws|docker|git|html|css)\b)\s*[:\-|]\s*([⭐★☆●○\s]+)',
            r'(\b(?:java|python|javascript|react|node|spring|boot|microservices)\b)\s*[:\-|]\s*([⭐★☆●○\s]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for tech, rating in matches:
                rating = rating.strip()
                # Only add if it looks like a rating, not a version
                if (rating.startswith('⭐') or rating.startswith('★') or 
                    rating.startswith('☆') or rating.startswith('●') or 
                    rating.startswith('○') or rating.startswith('•') or
                    '%' in rating or '/' in rating or '.' in rating):
                    skills.append(f"{tech.title()}: {rating}")
        
        return skills[:5]  # Top 5 skills

    def extract_domain_expertise(self, text: str) -> str:
        """Extract domain/industry expertise - ONLY if explicitly mentioned"""
        domains = {
            'fintech': 'Financial services and FinTech',
            'healthcare': 'Healthcare and Medical technology',
            'education': 'Education and E-learning',
            'ecommerce': 'Retail and E-commerce',
            'banking': 'Banking and Financial services',
            'insurance': 'Insurance and Risk management',
            'retail': 'Retail and Consumer goods',
            'manufacturing': 'Manufacturing and Supply chain',
            'logistics': 'Logistics and Transportation',
            'telecom': 'Telecommunications',
            'media': 'Media and Entertainment',
            'government': 'Government and Public sector'
        }
        
        text_lower = text.lower()
        
        # Only extract if domain is explicitly mentioned with experience/industry context
        for domain, description in domains.items():
            # Look for exact domain word with experience context
            if re.search(rf'\b{domain}\b.*?(?:experience|industry|sector|domain|expertise|professional|work)', text_lower):
                return f"Domain Expertise: {description}"
            elif re.search(rf'(?:experience|industry|sector|domain|expertise|professional|work).*?\b{domain}\b', text_lower):
                return f"Domain Expertise: {description}"
        
        return None

    def extract_projects(self, text: str) -> str:
        """Extract project information - ONLY if explicitly mentioned"""
        # Only look for explicit project mentions - be very specific
        project_patterns = [
            r'\bproject[s]?\s*(?:title|name)?[:\-]?\s*([^.]+?)(?:\.|$)',
            r'\bdeveloped?\s+(?:a\s+)?([^.]{10,50}?(?:project|application|system|platform))',
            r'\bbuilt?\s+(?:a\s+)?([^.]{10,50}?(?:project|application|system|platform))',
            r'\bcreated?\s+(?:a\s+)?([^.]{10,50}?(?:project|application|system|platform))',
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                project_name = matches[0].strip()[:50]
                # Clean project name - remove trailing words
                project_name = re.sub(r'\s+(?:and|or|with|for|in|on|at)\s+.*$', '', project_name, flags=re.IGNORECASE)
                # Exclude common non-project words
                exclude_words = ['projects', 'complex', 'teams', 'environments', 'applications', 'systems', 'lifecycle', 'design', 'implementation', 'integration']
                if (len(project_name) > 5 and 
                    not any(exclude_word.lower() in project_name.lower() for exclude_word in exclude_words)):
                    return f"Projects: {project_name.title()}"
        
        # Don't auto-generate project info - only return if explicitly found
        return None

    def generate_summary(self, text: str) -> str:
        """Generate RAG-based summary"""
        if not text or len(text.strip()) < 20:
            return "• No valid resume content found"
        
        # Clean text minimally - preserve original formatting
        text_clean = text.replace('\r', ' ')
        text_clean = re.sub(r'\n+', '\n', text_clean)
        
        # Extract information using RAG approach
        tech_skills = self.extract_tech_skills(text_clean)
        domain_expertise = self.extract_domain_expertise(text_clean)
        projects = self.extract_projects(text_clean)
        
        # Build summary - prioritize original text
        summary_points = []
        
        # Add original bullet points from text first (preserve stars)
        lines = text_clean.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 15 and not any(skip in line.lower() for skip in ['email', 'phone', 'contact', 'address', '@', 'http', 'www', 'linkedin']):
                summary_points.append(line)
        
        # Add tech skills if not already in summary
        if tech_skills:
            for skill in tech_skills:
                if not any(skill.split(':')[0] in point for point in summary_points):
                    summary_points.append(skill)
        
        # Only add domain if explicitly found AND mentioned in text
        if domain_expertise:
            domain_lower = domain_expertise.lower()
            if any(domain_word in text_clean.lower() for domain_word in ['healthcare', 'enterprise', 'fintech', 'banking', 'retail', 'education']):
                if not any(domain_expertise in point for point in summary_points):
                    summary_points.append(domain_expertise)
        
        # Only add projects if explicitly found AND mentioned in text
        if projects:
            project_lower = projects.lower()
            if any(project_word in text_clean.lower() for project_word in ['project', 'application', 'system', 'platform', 'software']):
                if not any(projects in point for point in summary_points):
                    summary_points.append(projects)
        
        # Format and return (preserve original formatting)
        return "\n".join(summary_points[:6])

# Global RAG instance
rag_processor = ResumeRAG()

def create_rag_summary(text: str) -> str:
    """Create RAG-based resume summary"""
    return rag_processor.generate_summary(text)
