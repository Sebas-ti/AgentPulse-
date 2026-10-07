"""AgentPulse command line interface."""

import typer

app = typer.Typer(
    name="agentpulse",
    help="AgentPulse CLI for evaluation and tracing",
    no_args_is_help=True,
)

eval_app = typer.Typer(
    name="eval",
    help="Run and manage evaluation suites",
    no_args_is_help=True,
)
app.add_typer(eval_app, name="eval")


@eval_app.command("run")
def eval_run(
    dataset: str = typer.Option(..., "--dataset", "-d", help="Dataset identifier or path"),
    threshold: float = typer.Option(0.8, "--threshold", "-t", help="Minimum passing score"),
) -> None:
    """Run an evaluation suite against a dataset."""
    typer.echo(f"Running evaluation against dataset '{dataset}' with threshold {threshold}...")
    # Will be connected to judge runner in Phase 4
    typer.echo("Evaluation completed successfully.")


@app.command("version")
def version() -> None:
    """Display AgentPulse CLI version."""
    typer.echo("AgentPulse CLI v0.1.0")


if __name__ == "__main__":
    app()
