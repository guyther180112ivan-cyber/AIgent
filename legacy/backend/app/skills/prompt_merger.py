import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptMerger:
    """
    Merges multiple skill prompts into a single coherent system prompt.
    Handles priority, conflicts, and optimization.
    """
    
    def __init__(self):
        # Merge strategies
        self.merge_strategies = {
            "priority": self._merge_by_priority,
            "category": self._merge_by_category,
            "sequential": self._merge_sequential,
            "weighted": self._merge_weighted
        }
        
        # Default strategy
        self.default_strategy = "priority"
        
        # Conflict resolution patterns
        self.conflict_patterns = [
            r"You are\s+(a|an)\s+(\w+)",
            r"Your name is\s+(\w+)",
            r"You should\s+(\w+)",
            r"Always\s+(\w+)",
            r"Never\s+(\w+)"
        ]
        
        # Section templates
        self.section_templates = {
            "identity": "## Agent Identity\n{content}",
            "behavior": "## Behavioral Guidelines\n{content}",
            "capabilities": "## Capabilities\n{content}",
            "constraints": "## Constraints\n{content}",
            "context": "## Context\n{content}"
        }
    
    async def merge_prompts(
        self,
        skills: List[Dict[str, Any]],
        strategy: str = "priority",
        max_length: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Merge multiple skill prompts into a single system prompt.
        
        Args:
            skills: List of skill dictionaries
            strategy: Merge strategy to use
            max_length: Maximum length of the merged prompt
            context: Additional context for merging
            
        Returns:
            Merged system prompt
        """
        try:
            if not skills:
                return "You are a helpful AI assistant."
            
            # Validate strategy
            if strategy not in self.merge_strategies:
                strategy = self.default_strategy
            
            # Sort skills based on strategy
            sorted_skills = self._sort_skills(skills, strategy)
            
            # Render skill templates
            rendered_skills = []
            for skill in sorted_skills:
                rendered = await self._render_skill_template(skill)
                if rendered:
                    rendered_skills.append({
                        "skill": skill,
                        "rendered": rendered,
                        "priority": skill.get("priority", 0),
                        "proficiency": skill.get("proficiency_level", 1)
                    })
            
            # Merge using strategy
            merged_prompt = await self.merge_strategies[strategy](rendered_skills, context)
            
            # Add context if provided
            if context:
                merged_prompt = await self._add_context(merged_prompt, context)
            
            # Optimize length
            if max_length and len(merged_prompt) > max_length:
                merged_prompt = await self._optimize_length(merged_prompt, max_length)
            
            # Validate and clean
            merged_prompt = await self._validate_and_clean(merged_prompt)
            
            logger.debug(f"Merged {len(skills)} skills into prompt ({len(merged_prompt)} chars)")
            return merged_prompt
            
        except Exception as e:
            logger.error(f"Error merging prompts: {str(e)}")
            return "You are a helpful AI assistant."
    
    def _sort_skills(self, skills: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
        """Sort skills based on the chosen strategy."""
        if strategy == "priority":
            # Sort by priority (descending) then proficiency (descending)
            return sorted(
                skills,
                key=lambda x: (x.get("priority", 0), x.get("proficiency_level", 1)),
                reverse=True
            )
        elif strategy == "category":
            # Sort by category then priority
            return sorted(
                skills,
                key=lambda x: (x.get("category", ""), x.get("priority", 0)),
                reverse=True
            )
        elif strategy == "weighted":
            # Sort by weighted score (priority * proficiency)
            return sorted(
                skills,
                key=lambda x: x.get("priority", 0) * x.get("proficiency_level", 1),
                reverse=True
            )
        else:  # sequential
            # Keep original order
            return skills
    
    async def _render_skill_template(self, skill: Dict[str, Any]) -> str:
        """Render skill template with configuration."""
        template = skill.get("system_prompt_template", "")
        config = skill.get("config", {})
        
        if not template:
            return skill.get("description", "")
        
        try:
            # Substitute template variables
            rendered = template
            for key, value in config.items():
                placeholder = f"{{{key}}}"
                if placeholder in rendered:
                    rendered = rendered.replace(placeholder, str(value))
            
            # Check for missing variables
            missing_vars = re.findall(r'\{([^}]+)\}', rendered)
            if missing_vars:
                logger.warning(f"Missing variables in skill {skill['name']}: {missing_vars}")
                for var in missing_vars:
                    rendered = rendered.replace(f"{{{var}}}", f"[MISSING: {var}]")
            
            return rendered
            
        except Exception as e:
            logger.error(f"Error rendering skill template for {skill['name']}: {str(e)}")
            return f"Error rendering skill template: {str(e)}"
    
    async def _merge_by_priority(
        self,
        rendered_skills: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Merge prompts by priority, resolving conflicts in favor of higher priority."""
        if not rendered_skills:
            return ""
        
        # Start with the highest priority skill as base
        base_prompt = rendered_skills[0]["rendered"]
        
        # Merge other skills, resolving conflicts
        for skill_data in rendered_skills[1:]:
            skill_prompt = skill_data["rendered"]
            merged_prompt = await self._resolve_conflicts(base_prompt, skill_prompt)
            base_prompt = merged_prompt
        
        return base_prompt
    
    async def _merge_by_category(
        self,
        rendered_skills: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Merge prompts by category, organizing them into sections."""
        # Group by category
        categories = {}
        for skill_data in rendered_skills:
            category = skill_data["skill"].get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(skill_data)
        
        # Build prompt with sections
        sections = []
        
        # Identity section (highest priority from general category)
        general_skills = categories.get("general", [])
        if general_skills:
            identity_content = await self._extract_identity_content(general_skills[0]["rendered"])
            sections.append(self.section_templates["identity"].format(content=identity_content))
        
        # Capabilities section by category
        for category, skills in categories.items():
            if category == "general":
                continue
            
            category_content = []
            for skill_data in skills:
                content = await self._extract_capabilities_content(skill_data["rendered"])
                if content:
                    category_content.append(f"**{skill_data['skill']['name']}**: {content}")
            
            if category_content:
                sections.append(f"## {category.title()}\n" + "\n".join(category_content))
        
        # Behavioral guidelines
        all_behaviors = []
        for skill_data in rendered_skills:
            behaviors = await self._extract_behavioral_content(skill_data["rendered"])
            if behaviors:
                all_behaviors.extend(behaviors)
        
        if all_behaviors:
            sections.append(self.section_templates["behavior"].format(content="\n".join(all_behaviors)))
        
        return "\n\n".join(sections)
    
    async def _merge_sequential(
        self,
        rendered_skills: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Merge prompts sequentially, maintaining order."""
        sections = []
        
        for skill_data in rendered_skills:
            skill_name = skill_data["skill"]["name"]
            skill_prompt = skill_data["rendered"]
            
            # Add skill as a section
            sections.append(f"## {skill_name}\n{skill_prompt}")
        
        return "\n\n".join(sections)
    
    async def _merge_weighted(
        self,
        rendered_skills: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Merge prompts with weighted influence based on proficiency and priority."""
        # Calculate weights
        total_weight = sum(
            skill["priority"] * skill["proficiency"]
            for skill in rendered_skills
        )
        
        if total_weight == 0:
            return await self._merge_sequential(rendered_skills, context)
        
        # Extract and weight content
        content_sections = {
            "identity": [],
            "behavior": [],
            "capabilities": []
        }
        
        for skill_data in rendered_skills:
            weight = (skill["priority"] * skill["proficiency"]) / total_weight
            skill_prompt = skill_data["rendered"]
            
            # Extract different types of content
            identity = await self._extract_identity_content(skill_prompt)
            behavior = await self._extract_behavioral_content(skill_prompt)
            capabilities = await self._extract_capabilities_content(skill_prompt)
            
            if identity:
                content_sections["identity"].append((identity, weight))
            if behavior:
                content_sections["behavior"].extend([(b, weight) for b in behavior])
            if capabilities:
                content_sections["capabilities"].append((capabilities, weight))
        
        # Build weighted prompt
        sections = []
        
        # Identity (highest weighted)
        if content_sections["identity"]:
            best_identity = max(content_sections["identity"], key=lambda x: x[1])[0]
            sections.append(self.section_templates["identity"].format(content=best_identity))
        
        # Capabilities (weighted combination)
        if content_sections["capabilities"]:
            capabilities_text = "\n".join([
                f"- {content}" for content, weight in content_sections["capabilities"]
            ])
            sections.append(self.section_templates["capabilities"].format(content=capabilities_text))
        
        # Behavior (weighted combination)
        if content_sections["behavior"]:
            behavior_text = "\n".join([
                f"- {content}" for content, weight in content_sections["behavior"]
            ])
            sections.append(self.section_templates["behavior"].format(content=behavior_text))
        
        return "\n\n".join(sections)
    
    async def _resolve_conflicts(self, base_prompt: str, new_prompt: str) -> str:
        """Resolve conflicts between two prompts."""
        # Extract conflicting statements
        conflicts = []
        
        for pattern in self.conflict_patterns:
            base_matches = re.findall(pattern, base_prompt, re.IGNORECASE)
            new_matches = re.findall(pattern, new_prompt, re.IGNORECASE)
            
            if base_matches and new_matches:
                conflicts.append({
                    "pattern": pattern,
                    "base": base_matches,
                    "new": new_matches
                })
        
        # If no conflicts, simply concatenate
        if not conflicts:
            return f"{base_prompt}\n\n{new_prompt}"
        
        # Resolve conflicts by keeping base prompt (higher priority)
        # but adding non-conflicting parts from new prompt
        resolved_prompt = base_prompt
        
        # Add non-conflicting sentences from new prompt
        new_sentences = re.split(r'[.!?]+', new_prompt)
        for sentence in new_sentences:
            sentence = sentence.strip()
            if sentence and not self._is_conflicting_sentence(sentence, conflicts):
                resolved_prompt += f" {sentence}."
        
        return resolved_prompt
    
    def _is_conflicting_sentence(self, sentence: str, conflicts: List[Dict[str, Any]]) -> bool:
        """Check if a sentence contains conflicting statements."""
        for conflict in conflicts:
            for match in conflict["new"]:
                if match.lower() in sentence.lower():
                    return True
        return False
    
    async def _extract_identity_content(self, prompt: str) -> str:
        """Extract identity-related content from prompt."""
        # Look for identity statements
        identity_patterns = [
            r"You are\s+(a|an)\s+([^,.!?]+)",
            r"Your name is\s+([^,.!?]+)",
            r"I am\s+(a|an)\s+([^,.!?]+)",
            r"My name is\s+([^,.!?]+)"
        ]
        
        for pattern in identity_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    async def _extract_behavioral_content(self, prompt: str) -> List[str]:
        """Extract behavioral guidelines from prompt."""
        behaviors = []
        
        # Look for behavioral statements
        behavior_patterns = [
            r"You should\s+([^,.!?]+)",
            r"Always\s+([^,.!?]+)",
            r"Never\s+([^,.!?]+)",
            r"Make sure to\s+([^,.!?]+)",
            r"Remember to\s+([^,.!?]+)"
        ]
        
        for pattern in behavior_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            behaviors.extend(matches)
        
        return behaviors
    
    async def _extract_capabilities_content(self, prompt: str) -> str:
        """Extract capability descriptions from prompt."""
        # Look for capability statements
        capability_patterns = [
            r"You can\s+([^,.!?]+)",
            r"You are able to\s+([^,.!?]+)",
            r"You have the ability to\s+([^,.!?]+)",
            r"Your skills include\s+([^,.!?]+)"
        ]
        
        for pattern in capability_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # If no specific capability found, return a summary
        sentences = re.split(r'[.!?]+', prompt)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Filter out very short sentences
                return sentence
        
        return ""
    
    async def _add_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Add context information to the prompt."""
        context_sections = []
        
        if "current_time" in context:
            context_sections.append(f"Current time: {context['current_time']}")
        
        if "user_context" in context:
            user_context = context["user_context"]
            if isinstance(user_context, dict):
                for key, value in user_context.items():
                    context_sections.append(f"User {key}: {value}")
            else:
                context_sections.append(f"User context: {user_context}")
        
        if "conversation_context" in context:
            context_sections.append(f"Conversation context: {context['conversation_context']}")
        
        if context_sections:
            context_text = "\n".join(context_sections)
            prompt = f"{prompt}\n\n{self.section_templates['context'].format(content=context_text)}"
        
        return prompt
    
    async def _optimize_length(self, prompt: str, max_length: int) -> str:
        """Optimize prompt length while preserving important content."""
        if len(prompt) <= max_length:
            return prompt
        
        # Split into sections
        sections = re.split(r'\n## ', prompt)
        
        # Prioritize sections
        priority_sections = ["Agent Identity", "Behavioral Guidelines"]
        optimized_sections = []
        current_length = 0
        
        # Add high priority sections first
        for section in sections:
            if not section.strip():
                continue
            
            section_name = section.split('\n')[0] if '\n' in section else section
            if section_name in priority_sections:
                if current_length + len(section) <= max_length - 100:
                    optimized_sections.append(f"## {section}")
                    current_length += len(section)
        
        # Add other sections as space allows
        for section in sections:
            if not section.strip():
                continue
            
            section_name = section.split('\n')[0] if '\n' in section else section
            if section_name in priority_sections:
                continue
            
            if current_length + len(section) <= max_length - 50:
                optimized_sections.append(f"## {section}")
                current_length += len(section)
            else:
                # Truncate section
                remaining_space = max_length - current_length - 50
                if remaining_space > 100:
                    truncated = section[:remaining_space] + "..."
                    optimized_sections.append(f"## {truncated}")
                break
        
        result = "\n".join(optimized_sections)
        
        # Add truncation notice
        if len(result) < len(prompt):
            result += "\n\n[Note: Some content was truncated to fit within length limits]"
        
        return result
    
    async def _validate_and_clean(self, prompt: str) -> str:
        """Validate and clean the merged prompt."""
        # Remove excessive whitespace
        prompt = re.sub(r'\n\s*\n\s*\n', '\n\n', prompt)
        
        # Fix common formatting issues
        prompt = re.sub(r'\s*##\s*', '\n## ', prompt)
        prompt = re.sub(r'\s*\*\s*', '\n* ', prompt)
        
        # Ensure proper ending
        if not prompt.endswith('.'):
            prompt += '.'
        
        return prompt.strip()
    
    async def preview_merge(
        self,
        skills: List[Dict[str, Any]],
        strategy: str = "priority"
    ) -> Dict[str, Any]:
        """
        Preview the merge without actually performing it.
        
        Returns:
            Dictionary with merge preview information
        """
        try:
            # Sort skills
            sorted_skills = self._sort_skills(skills, strategy)
            
            # Render templates
            rendered_skills = []
            for skill in sorted_skills:
                rendered = await self._render_skill_template(skill)
                rendered_skills.append({
                    "skill": skill,
                    "rendered": rendered,
                    "length": len(rendered)
                })
            
            # Calculate statistics
            total_length = sum(rs["length"] for rs in rendered_skills)
            avg_length = total_length / len(rendered_skills) if rendered_skills else 0
            
            # Detect potential conflicts
            conflicts = []
            for i, rs1 in enumerate(rendered_skills):
                for rs2 in rendered_skills[i+1:]:
                    if await self._has_conflicts(rs1["rendered"], rs2["rendered"]):
                        conflicts.append({
                            "skill1": rs1["skill"]["name"],
                            "skill2": rs2["skill"]["name"],
                            "type": "content_conflict"
                        })
            
            return {
                "strategy": strategy,
                "skills_count": len(skills),
                "sorted_skills": [rs["skill"]["name"] for rs in rendered_skills],
                "total_length": total_length,
                "average_length": avg_length,
                "conflicts": conflicts,
                "estimated_final_length": int(total_length * 0.8),  # Rough estimate
                "recommendations": self._generate_recommendations(rendered_skills, conflicts)
            }
            
        except Exception as e:
            logger.error(f"Error previewing merge: {str(e)}")
            return {
                "error": str(e),
                "strategy": strategy,
                "skills_count": len(skills)
            }
    
    async def _has_conflicts(self, prompt1: str, prompt2: str) -> bool:
        """Check if two prompts have conflicts."""
        for pattern in self.conflict_patterns:
            matches1 = re.findall(pattern, prompt1, re.IGNORECASE)
            matches2 = re.findall(pattern, prompt2, re.IGNORECASE)
            
            if matches1 and matches2:
                # Check for actual conflicts (not just matches)
                for match1 in matches1:
                    for match2 in matches2:
                        if match1.lower() != match2.lower():
                            return True
        
        return False
    
    def _generate_recommendations(
        self,
        rendered_skills: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for better merging."""
        recommendations = []
        
        # Check for very long prompts
        long_skills = [rs for rs in rendered_skills if rs["length"] > 1000]
        if long_skills:
            recommendations.append(f"Consider shortening {len(long_skills)} skill(s) with long prompts")
        
        # Check for conflicts
        if conflicts:
            recommendations.append(f"Resolve {len(conflicts)} potential conflicts between skills")
        
        # Check for similar skills
        skill_names = [rs["skill"]["name"] for rs in rendered_skills]
        if len(skill_names) != len(set(skill_names)):
            recommendations.append("Remove duplicate or very similar skills")
        
        # Check for priority distribution
        priorities = [rs["skill"].get("priority", 0) for rs in rendered_skills]
        if len(set(priorities)) < len(priorities) / 2:
            recommendations.append("Consider using more diverse priority values")
        
        return recommendations
