import os
import stat

def test_folder_permissions(folder_path):
    print(f"Folder: {folder_path}")
    if not os.path.exists(folder_path):
        print("Folder does not exist.")
        return

    # Check folder permissions
    st = os.stat(folder_path)
    print(f"Permissions: {stat.filemode(st.st_mode)}")

    # Check file read permissions
    file_path = os.path.join(folder_path, "test.txt")
    if os.path.isfile(file_path):
        try:
            with open(file_path, "r") as f:
                print("Read access: Yes")
        except Exception as e:
            print(f"Read access: No ({e})")
    else:
        print("File does not exist.")

    # Check file write permissions
    file_path = os.path.join(folder_path, "test_write.txt")
    try:
        with open(file_path, "w") as f:
            f.write("Test write.")
        print("Write access: Yes")
    except Exception as e:
        print(f"Write access: No ({e})")

    print("")

# Test various folders
test_folder_permissions("/config/")
test_folder_permissions("/addons/")
test_folder_permissions("/config/logs/")
test_folder_permissions("/config/www/")
test_folder_permissions("/config/custom_components/")
test_folder_permissions("/config/venv/")
test_folder_permissions("/config/configuration.yaml")
test_folder_permissions("/config/home-assistant.log")
