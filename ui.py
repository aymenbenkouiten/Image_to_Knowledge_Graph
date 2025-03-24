import base64
import os
from datetime import datetime
import streamlit as st
from main import *
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
        background-attachment: fixed;
        animation: fadeIn 2s;
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

def plt_KnGraph(concepts):
    G = KnGraph_extract(concepts)
    color_map = ['lightgreen' if node in concepts else 'yellow' for node in G.nodes()]
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G, k=0.4)
    nx.draw(G, pos, node_color=color_map, with_labels=True)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'label'))
    plt.title("Knowledge Graph")
    plt.axis("off")
    st.pyplot(plt)

def main():
    set_png_as_page_bg('images/background.jpg')
    st.markdown("""
        <div style="text-align: center; animation: slideIn 1.5s;">
            <h1 style="color: #FF6347; font-size: 3em;">🔍 Object Detection & Knowledge Graph 🌐</h1>
            <p style="font-size: 1.2em; color: #FFD700;">Explore AI-powered object detection and visualize concepts in a Knowledge Graph.</p>
        </div>
        <style>
            @keyframes slideIn {
                from {transform: translateY(-50px); opacity: 0;}
                to {transform: translateY(0); opacity: 1;}
            }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.header("Options")
    use_webcam = st.sidebar.checkbox("Use Webcam", help="Toggle to capture an image using your webcam.")

    st.sidebar.subheader("Processing Options")
    st.sidebar.selectbox("Detection Algorithm", ["YOLOv11"], help="Select the object detection algorithm.")
    st.sidebar.slider("Confidence Threshold", 0.0, 0.5, 1.0, step=0.05, help="Set the confidence threshold for detection.")

    st.sidebar.subheader("Visualization")
    st.sidebar.multiselect("Graph Customization", ["Show Labels", "Highlight Important Nodes", "Adjust Layout"], help="Customize the visualization of the Knowledge Graph.")
    st.sidebar.color_picker("Node Color", "#00FF00", help="Select the default color for nodes in the graph.")

    uploaded_file = None
    image_path = None

    if not use_webcam:
        uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "png"], help="Choose an image for object detection.")
        if uploaded_file is not None:
            temp_dir = "temp_images"
            os.makedirs(temp_dir, exist_ok=True)
            image_path = os.path.join(temp_dir, uploaded_file.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
    else:
        picture = st.camera_input("Take a Picture")
        if picture:
            temp_dir = "temp_images"
            os.makedirs(temp_dir, exist_ok=True)
            image_path = os.path.join(temp_dir, "webcam_image.png")
            with open(image_path, "wb") as f:
                f.write(picture.getbuffer())

    if image_path is not None:
        st.image(image_path, caption='Uploaded Image', use_column_width=True)

        concepts = yolo_detect_objects(image_path)
        concepts = list(set(concepts))

        st.markdown("""
            <style>
            .custom-table {
                width: 100%;
                background-color: #2B2B2B;
                color: white;
                border-radius: 10px;
                overflow: hidden;
                text-align: center;
            }
            .custom-table th, .custom-table td {
                padding: 10px;
            }
            .custom-table th {
                background-color: #1E1E1E;
                font-weight: bold;
            }
            .custom-table tr:nth-child(even) {
                background-color: #333333;
            }
            </style>
        """, unsafe_allow_html=True)
        st.subheader("🔎 Detected Concepts")
        st.write('<table class="custom-table"><tr><th>Concept</th></tr>' +
                 ''.join([f'<tr><td>{concept}</td></tr>' for concept in concepts]) +
                 '</table>', unsafe_allow_html=True)

        if st.button("📥 Download Detected Objects", help="Download the detected objects as a text file."):
            text_file = "detected_concepts.txt"
            with open(text_file, "w") as f:
                f.write("\n".join(concepts))
            with open(text_file, "rb") as f:
                st.download_button(
                    label="Download Detected Objects as Text",
                    data=f,
                    file_name="detected_concepts.txt",
                    mime="text/plain"
                )

        if not concepts:
            st.error("No objects detected in the image. Please try another image.")
            return

        option = st.selectbox(
            '🎨 Choose what to display:',
            ('Knowledge Graph', 'RDF Description'),
            help="Select between visualizing the Knowledge Graph or viewing RDF descriptions of detected concepts."
        )

        if option == 'Knowledge Graph':
            rdf_graph = get_relations_from_conceptnet(concepts)
            insert_rdf_to_fuseki(rdf_graph)
            plt_KnGraph(concepts)
        elif option == 'RDF Description':
            description = generate_rdf_description(concepts)
            st.text_area("📝 RDF Description:", description, height=500)

if __name__ == '__main__':
    main()
