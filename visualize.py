# visualize_graph.py

from pathlib import Path

# Import the final compiled graph object from your graph.py file
from graph import graph

print("[INFO] Generating graph visualization...")

try:
    # Get the graph visualization as PNG bytes
    image_bytes = graph.get_graph(xray=True).draw_mermaid_png()

    # Define the output file path
    output_path = Path("graph_visualization.png")

    # Write the bytes to a file
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    print(f"[SUCCESS] Graph visualization saved to: {output_path}")
    print("[INFO] You can now open this image file to see your agent's flowchart.")

except Exception as e:
    print(f"[ERROR] Failed to generate graph visualization: {e}")
    print("[INFO] Please ensure you have the necessary dependencies installed (see instructions).")
