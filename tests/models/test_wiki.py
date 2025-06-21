from models.enums import SectionRestrictionType
from models.wiki import (
    WikiPage,
    WikiPageVersion,
    WikiPageVersionStatus,
    WikiSection,
    WikiTag,
    get_or_create_wiki_page,
)


def test_new_wiki_page_with_version_and_sections(db, new_user):
    """Test creation of a new WikiPage with version and sections."""
    # Create a wiki page
    page = WikiPage(slug="test-page", title="Test Page")

    db.session.add(page)
    db.session.commit()

    # Create a version
    version = WikiPageVersion(
        page_slug=page.slug,
        version_number=1,
        status=WikiPageVersionStatus.PUBLISHED,
        created_by=new_user.id,
    )

    db.session.add(version)
    db.session.commit()

    # Create sections
    section1 = WikiSection(
        version_id=version.id,
        id=1,
        order=0,
        title="Introduction",
        content="This is the introduction section.",
        restriction_type=SectionRestrictionType.ROLE,
        restriction_value_list=["admin", "user_admin"],
    )

    section2 = WikiSection(
        version_id=version.id,
        id=2,
        order=1,
        title="Content",
        content="This is the main content section.",
    )

    db.session.add_all([section1, section2])
    db.session.commit()

    # Create tags
    tag1 = WikiTag(name="test")
    tag2 = WikiTag(name="documentation")
    db.session.add_all([tag1, tag2])
    db.session.commit()

    # Add tags to page
    page.tags = [tag1, tag2]
    db.session.commit()

    # Retrieve and assert
    retrieved_page = WikiPage.query.filter_by(slug="test-page").first()

    assert retrieved_page is not None
    assert retrieved_page.slug == "test-page"
    assert retrieved_page.title == "Test Page"

    # Check versions relationship
    assert retrieved_page.versions.count() == 1
    retrieved_version = retrieved_page.versions.first()
    assert retrieved_version.version_number == 1
    assert retrieved_version.status == WikiPageVersionStatus.PUBLISHED
    assert retrieved_version.created_by == new_user.id

    # Check sections relationship
    assert retrieved_version.sections.count() == 2
    sections = list(retrieved_version.sections)
    assert sections[0].title == "Introduction"
    assert sections[0].content == "This is the introduction section."
    assert sections[0].restriction_type == SectionRestrictionType.ROLE
    assert sections[0].restriction_value_list == ["admin", "user_admin"]
    assert sections[1].title == "Content"
    assert sections[1].content == "This is the main content section."

    # Check tags relationship
    assert len(retrieved_page.tags) == 2
    tag_names = [tag.name for tag in retrieved_page.tags]
    assert "test" in tag_names
    assert "documentation" in tag_names


def test_get_or_create_wiki_page(db, new_user):
    """Test the get_or_create_wiki_page helper function."""
    # Test creating a new page
    page = get_or_create_wiki_page("new-page", "New Page", new_user.id)
    db.session.commit()

    assert page is not None
    assert page.slug == "new-page"
    assert page.title == "New Page"

    # Check that version was created
    assert page.versions.count() == 1
    version = page.versions.first()
    assert version.version_number == 1
    assert version.status == WikiPageVersionStatus.PUBLISHED
    assert version.created_by == new_user.id

    # Check that section was created
    assert version.sections.count() == 1
    section = version.sections.first()
    assert section.title == "New Page"
    assert section.content == ""

    # Test getting existing page
    existing_page = get_or_create_wiki_page("new-page", "Different Title", new_user.id)
    assert existing_page == page  # Should return the same page
    assert existing_page.title == "New Page"  # Title should not change
