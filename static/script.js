function previewImage() {
    const input = document.getElementById("imageInput");
    const preview = document.getElementById("preview");
    const placeholder = document.getElementById("placeholder");

    const file = input.files[0];
    if (!file) return;

    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";
    placeholder.style.display = "none";
}

function uploadImage() {
    const input = document.getElementById("imageInput");
    const file = input.files[0];

    if (!file) {
        alert("Please upload an image first");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    fetch("/predict", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        const preview = document.getElementById("preview");
        const placeholder = document.getElementById("placeholder");

        preview.src = data.image + "?t=" + new Date().getTime();
        preview.style.display = "block";
        placeholder.style.display = "none";

        document.getElementById("rbcCount").innerText = data.counts.RBC || 0;
        document.getElementById("wbcCount").innerText = data.counts.WBC || 0;
        document.getElementById("plateletCount").innerText = data.counts.Platelets || 0;
    })
    .catch(() => {
        alert("Error processing image");
    });
}
