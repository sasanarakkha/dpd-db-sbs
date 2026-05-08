from scripts.rus_exporter.docs_check_ru import check_file


def test_docs_check_ru(tmp_path):
    # Setup
    docs_dir = tmp_path / "docs_rus"
    docs_dir.mkdir()

    img_dir = docs_dir / "assets" / "pics"
    img_dir.mkdir(parents=True)

    # Create target files
    live_md = docs_dir / "live.md"
    live_md.write_text("live")

    live_img = img_dir / "live.png"
    live_img.write_text("img")

    # Create index.md with various links
    index_md = docs_dir / "index.md"
    content = [
        "- [Live Link](live.md)",  # Should be preserved
        "- [Dead Link](dead.md)",  # Should be removed
        "- [Live Link with Anchor](live.md#top)",  # Should be preserved
        "- [Dead Link with Anchor](dead.md#top)",  # Should be removed
        "Prose with [Dead Link](dead.md)",  # Should be preserved (only list items auto-removed)
        "![Live Image](assets/pics/live.png)",  # Should be OK
        "![Dead Image](assets/pics/dead.png)",  # Should be reported
        "![Live Dark](assets/pics/live.png#only-dark)",  # Should be OK
        "![External](https://example.com/a.png)",  # Should be skipped
    ]
    index_md.write_text("\n".join(content))

    # Run check
    # We pass docs_dir to help the script find files if it's not running from the real project root
    broken_images = check_file(index_md)

    # Verification
    new_content = index_md.read_text().splitlines()

    assert "- [Live Link](live.md)" in new_content
    assert "- [Dead Link](dead.md)" not in new_content
    assert "- [Live Link with Anchor](live.md#top)" in new_content
    assert "- [Dead Link with Anchor](dead.md#top)" not in new_content
    assert "Prose with [Dead Link](dead.md)" in new_content

    assert len(broken_images) == 1
    assert "assets/pics/dead.png" in broken_images[0]
