# Minions AI

This is a tool to collect data and export them with agentic AI.

Just tell what you need and get the structured data in the `outuput` directory.

## Features

- Agentic AI for data collection
- Structured data export
- Self critique and improvement
- OPENAI API integration

## TODOs

- [x] Use Google API for search
- [x] Parse webapps and dynamic pages
- [x] Export to JSON
- [ ] Better user input and format request
- [ ] Integrate other LLMs (backends) and embedders (have a factory class to create LLM instance)
- [ ] Add more export formats (e.g., CSV, XML)
- [ ] Refine the workflow and better self reflection loop.
- [ ] Add docs and use cases + examples
- [ ] Enhance the terminal UI and make it cleaner (Loading, workflow steps, ...)
- [ ] Add a feature to add more search resources such as local docs, or a new tool for the data discovery phase, ... .
- [ ] Implement PostgresDB Checkpointer.