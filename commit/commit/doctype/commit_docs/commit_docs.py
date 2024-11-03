# Copyright (c) 2024, The Commit Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CommitDocs(Document):
	pass


@frappe.whitelist()
def get_docs_sidebar_parent_labels(id:str):
	'''
		Get the Parent Labels List of the Sidebar from Commit Docs
	'''

	# Get the Commit Docs Document
	commit_docs = frappe.get_doc('Commit Docs', id)

	parent_labels = []

	for sidebar in commit_docs.sidebar:
		parent_labels.append(sidebar.parent_label)

	parent_labels = list(set(parent_labels))

	parent_labels_obj = []
	for label in parent_labels:
		parent_labels_obj.append({
			'label': label,
			'value': label
		})

	return parent_labels_obj

@frappe.whitelist(allow_guest=True)
def get_commit_docs_details(route:str):
	'''
		Get the Commit Docs Details
		# 1. Get the Commit Docs Document from the route
		# 2. Check if the Commit Docs Document Published
		# 3. Return the Commit Docs Document
		# 4. Get The Sidebar Items for the Commit Docs
		# 5. Return the Sidebar Items
	'''

	# Check if the Commit Docs Document Exists
	if frappe.db.exists('Commit Docs',{'route':route}):

		# Check if the document is published
		if frappe.db.get_value('Commit Docs',{'route':route},'published'):

			# Get the Commit Docs Document
			commit_docs = frappe.get_doc('Commit Docs',{'route':route}).as_dict()

			# Get the Sidebar Items
			sidebar_items = get_sidebar_items(commit_docs.sidebar)

			# Get the Footer Items
			footer_items = get_footer_items(commit_docs.footer)

			# Get the Navbar Items
			navbar_items = get_navbar_items(commit_docs.navbar_items)
			
			# remove the sidebar from the commit_docs as it is not needed
			commit_docs.pop('sidebar')
			commit_docs.pop('footer')
			commit_docs.pop('navbar_items')

			return {
				'commit_docs': commit_docs,
				'sidebar_items': sidebar_items,
				'footer_items': footer_items,
				'navbar_items': navbar_items
			}

		else:
			return frappe.throw('Docs Not Published')
		
	else:
		return frappe.throw('Docs Not Found')


def get_footer_items(footer):
	'''
		Get the Footer Items
		# 1. Loop Over the Footer Items Which have Parent Label URL and Label
		# 2. Check if the Footer Item is Hide on Footer
		# 3. Return the Footer Items
	'''
	footer_obj = {}
	for footer_item in footer:
		if footer_item.hide_on_footer:
			continue

		if footer_item.parent_label not in footer_obj:
			footer_obj[footer_item.parent_label] = [
				{
					'label': footer_item.label,
					'url': footer_item.url
				}
			]
		else:
			footer_obj[footer_item.parent_label].append({
				'label': footer_item.label,
				'url': footer_item.url
			})
	
	return footer_obj

def get_navbar_items(navbar):
	'''
		Get the Navbar Items
		# 1. Loop Over the Navbar Items Which have Label, Parent Label, URL
		# 2. Check if the Navbar Item is Hide on Navbar
		# 3. Navbar Items are Nothing But Buttons which are displayed on the Navbar
		# 4. Parent Label is not Mandatory it is nothing but Like as Menu Button which has Sub Buttons
	'''

	navbar_obj = {}
	for navbar_item in navbar:
		if navbar_item.hide_on_navbar:
			continue
		
		# If the Item don't have parent label then add it as Object in the Navbar Object with the type as Button
		# If the Item have parent label then check if navbar_obj have the parent label if not then add it in array as item with type as Menu
		if not navbar_item.parent_label:
			if navbar_item.label not in navbar_obj:
				navbar_obj[navbar_item.label] = {
					'type':'Menu',
					'items': [{
						'label': navbar_item.label,
						'url': navbar_item.url,
						'type': 'Button',
						'icon': navbar_item.icon,
						'open_in_new_tab': navbar_item.open_in_new_tab
					}]
				}
			else:
				navbar_obj[navbar_item.label]['items'].append({
					'label': navbar_item.label,
					'url': navbar_item.url,
					'type': 'Button',
					'icon': navbar_item.icon,
					'open_in_new_tab': navbar_item.open_in_new_tab
				})
		else:
			navbar_obj[navbar_item.label] = {
				'label': navbar_item.label,
				'url': navbar_item.url,
				'type': 'Button',
				'icon': navbar_item.icon,
				'open_in_new_tab': navbar_item.open_in_new_tab
			}

	return navbar_obj

def get_sidebar_items(sidebar):
	'''
		Get the Sidebar Items
		# 1. Loop Over the Sidebar Items and Get the Commit Docs Page
		# 2. Check if the Commit Docs Page is Published and Permitted
		# 3. Check if the Commit Docs Page is Group Page
		# 4. If Group Page then treat it as a Group and Loop Over the Group Items and Get the Commit Docs Page
		# 2. Return the Sidebar Items
	'''
	sidebar_obj = {}
	for sidebar_item in sidebar:
		if sidebar_item.hide_on_sidebar:
			continue

		commit_docs_page = frappe.get_doc('Commit Docs Page',sidebar_item.docs_page)

		permitted = commit_docs_page.allow_guest or frappe.session.user != 'Guest'
		published = commit_docs_page.published
		is_group_page = commit_docs_page.is_group_page

		if not permitted or not published:
			continue

		if is_group_page:
			group_items = []
			for group_item in commit_docs_page.linked_pages:
				group_commit_docs_page = frappe.get_doc('Commit Docs Page',group_item.commit_docs_page)

				permitted = group_commit_docs_page.allow_guest or frappe.session.user != 'Guest'
				published = group_commit_docs_page.published

				if not permitted or not published:
					continue
				
				# Make the Array of the Group Items
				group_items.append({
					'name': group_commit_docs_page.name,
					'type': 'Docs Page',
					'title': group_commit_docs_page.title,
					'route': group_commit_docs_page.route,
					'badge': group_commit_docs_page.badge,
					'badge_color': group_commit_docs_page.badge_color,
					'icon': group_commit_docs_page.icon,
					'parent_name': commit_docs_page.name
				})
			
			if sidebar_item.parent_label not in sidebar_obj:
				sidebar_obj[sidebar_item.parent_label] = [
					{
						'name': commit_docs_page.name,
						'type': 'Docs Page',
						'title': commit_docs_page.title,
						'route': commit_docs_page.route,
						'badge': commit_docs_page.badge,
						'badge_color': commit_docs_page.badge_color,
						'icon': commit_docs_page.icon,
						'group_name': sidebar_item.parent_label,
						'is_group_page': is_group_page,
						'group_items': group_items
					}
				]

		if sidebar_item.parent_label not in sidebar_obj:
			sidebar_obj[sidebar_item.parent_label] = [
				{
					'name': commit_docs_page.name,
					'type': 'Docs Page',
					'title': commit_docs_page.title,
					'route': commit_docs_page.route,
					'badge': commit_docs_page.badge,
					'badge_color': commit_docs_page.badge_color,
					'icon': commit_docs_page.icon,
					'group_name': sidebar_item.parent_label
				}
			]
		else:
			sidebar_obj[sidebar_item.parent_label].append({
				'name': commit_docs_page.name,
				'type': 'Docs Page',
				'title': commit_docs_page.title,
				'route': commit_docs_page.route,
				'badge': commit_docs_page.badge,
				'badge_color': commit_docs_page.badge_color,
				'icon': commit_docs_page.icon,
				'group_name': sidebar_item.parent_label
			})

	return sidebar_obj