class ExactNameTemplateMatcher: #matches exact recipe name from recipe.json to accepted_recipe.json, returns the matched template if found, else None.
    def find_template(self, recipe_name, accepted_recipes):
        normalize = lambda name: " ".join(name.casefold().split())
        target = normalize(recipe_name)

        for template in accepted_recipes:
            if normalize(template.get("name", "")) == target:
                return template

        return None