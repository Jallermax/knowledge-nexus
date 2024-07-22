from graph_rag.processor.todoist_processor import TodoistProcessor

if __name__ == "__main__":
    print("Started experiments...")
    # gather_metadata(todoist_api)
    todoist = TodoistProcessor()
    labels = todoist.get_all_labels()
    print(labels)
    projects = todoist.get_all_projects()
    print(projects)
