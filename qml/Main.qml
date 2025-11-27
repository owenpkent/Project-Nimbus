import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import "components" as Comp
import "layouts" as Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 1024
    height: 600
    minimumWidth: 256
    minimumHeight: 150
    title: "Project Nimbus - QML UI"
    background: Rectangle { color: "black" }

    // Scale factor bound to Python bridge; default 1.0
    property real scaleFactor: controller ? controller.scaleFactor : 1.0
    
    // Current profile and layout type
    property string currentProfile: controller ? controller.getCurrentProfile() : "flight_simulator"
    property string layoutType: controller ? controller.getLayoutType() : "flight_sim"
    
    // Track available profiles for dynamic updates
    property var availableProfiles: controller ? controller.getAvailableProfiles() : []
    
    // Update when profile changes
    Connections {
        target: controller
        function onProfileChanged(profileId) {
            root.currentProfile = profileId
        }
        function onLayoutTypeChanged(newLayoutType) {
            root.layoutType = newLayoutType
        }
        function onProfilesListChanged() {
            // Refresh profile list when profiles are added/deleted
            root.availableProfiles = controller.getAvailableProfiles()
        }
        function onProfileSaved(success) {
            if (success) {
                saveNotification.show("Profile saved successfully")
            } else {
                saveNotification.show("Failed to save profile")
            }
        }
    }
    
    // Simple notification popup
    Rectangle {
        id: saveNotification
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 50
        width: notificationLabel.width + 40
        height: 40
        radius: 8
        color: "#333"
        border.color: "#555"
        border.width: 1
        opacity: 0
        z: 1000
        
        function show(message) {
            notificationLabel.text = message
            notificationAnimation.start()
        }
        
        Label {
            id: notificationLabel
            anchors.centerIn: parent
            color: "white"
            font.pixelSize: 14
        }
        
        SequentialAnimation {
            id: notificationAnimation
            NumberAnimation { target: saveNotification; property: "opacity"; to: 1; duration: 200 }
            PauseAnimation { duration: 2000 }
            NumberAnimation { target: saveNotification; property: "opacity"; to: 0; duration: 500 }
        }
    }

    // Save Profile As Dialog
    Dialog {
        id: saveAsDialog
        title: "Save Profile As"
        modal: true
        anchors.centerIn: parent
        width: 400
        height: 280
        
        background: Rectangle {
            color: "#2a2a2a"
            border.color: "#555"
            border.width: 1
            radius: 8
        }
        
        header: Label {
            text: saveAsDialog.title
            color: "white"
            font.pixelSize: 16
            font.bold: true
            padding: 16
            background: Rectangle { color: "#333"; radius: 8 }
        }
        
        contentItem: Column {
            spacing: 16
            padding: 16
            
            Column {
                spacing: 6
                width: parent.width - 32
                
                Label {
                    text: "Profile Name:"
                    color: "#ccc"
                    font.pixelSize: 13
                }
                Basic.TextField {
                    id: profileNameField
                    width: parent.width
                    placeholderText: "Enter profile name..."
                    color: "white"
                    font.pixelSize: 14
                    background: Rectangle {
                        color: "#1a1a1a"
                        border.color: profileNameField.activeFocus ? "#4a9eff" : "#555"
                        border.width: 1
                        radius: 4
                    }
                }
            }
            
            Column {
                spacing: 6
                width: parent.width - 32
                
                Label {
                    text: "Description (optional):"
                    color: "#ccc"
                    font.pixelSize: 13
                }
                Basic.TextField {
                    id: profileDescField
                    width: parent.width
                    placeholderText: "Enter description..."
                    color: "white"
                    font.pixelSize: 14
                    background: Rectangle {
                        color: "#1a1a1a"
                        border.color: profileDescField.activeFocus ? "#4a9eff" : "#555"
                        border.width: 1
                        radius: 4
                    }
                }
            }
        }
        
        footer: Row {
            spacing: 12
            padding: 16
            layoutDirection: Qt.RightToLeft
            
            Basic.Button {
                text: "Save"
                enabled: profileNameField.text.trim().length > 0
                onClicked: {
                    var newId = controller.createProfileAs(
                        profileNameField.text.trim(),
                        profileDescField.text.trim()
                    )
                    if (newId !== "") {
                        saveNotification.show("Profile '" + profileNameField.text.trim() + "' created")
                        controller.switchProfile(newId)
                    } else {
                        saveNotification.show("Failed to create profile")
                    }
                    profileNameField.text = ""
                    profileDescField.text = ""
                    saveAsDialog.close()
                }
                contentItem: Label {
                    text: parent.text
                    color: parent.enabled ? "white" : "#888"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 80
                    implicitHeight: 32
                    color: parent.enabled ? (parent.down ? "#2563eb" : "#3b82f6") : "#444"
                    radius: 4
                }
            }
            
            Basic.Button {
                text: "Cancel"
                onClicked: {
                    profileNameField.text = ""
                    profileDescField.text = ""
                    saveAsDialog.close()
                }
                contentItem: Label {
                    text: parent.text
                    color: "#ccc"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 80
                    implicitHeight: 32
                    color: parent.down ? "#444" : "#333"
                    border.color: "#555"
                    border.width: 1
                    radius: 4
                }
            }
        }
        
        onOpened: {
            profileNameField.text = ""
            profileDescField.text = ""
            profileNameField.forceActiveFocus()
        }
    }

    // Menus (safe dark mode for top bar only)
    menuBar: MenuBar {
        background: Rectangle { color: "#2a2a2a" }
        delegate: MenuBarItem {
            id: control
            implicitHeight: 30
            contentItem: Label {
                text: control.text
                color: "white"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                leftPadding: 10
                rightPadding: 10
            }
            background: Rectangle {
                color: control.hovered ? "#3a3a3a" : "#2a2a2a"
            }
        }

        Menu {
            id: fileMenu
            title: qsTr("File")
            
            // Profile submenu
            Menu {
                id: profileMenu
                title: qsTr("Profile")
                
                Instantiator {
                    id: profileInstantiator
                    model: root.availableProfiles
                    delegate: MenuItem {
                        text: modelData.name
                        checkable: true
                        checked: root.currentProfile === modelData.id
                        onTriggered: {
                            fileMenu.close()
                            Qt.callLater(function() {
                                if (controller) controller.switchProfile(modelData.id)
                            })
                        }
                    }
                    onObjectAdded: function(index, object) { profileMenu.insertItem(index, object) }
                    onObjectRemoved: function(index, object) { profileMenu.removeItem(object) }
                }
            }
            
            MenuItem {
                text: qsTr("Save Profile")
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        if (controller) controller.saveCurrentProfile()
                    })
                }
            }
            MenuItem {
                text: qsTr("Save Profile As...")
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        saveAsDialog.open()
                    })
                }
            }
            MenuItem {
                text: qsTr("Reset Profile to Defaults")
                enabled: controller ? controller.isBuiltinProfile(root.currentProfile) : false
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        if (controller) {
                            controller.resetProfile(root.currentProfile)
                            saveNotification.show("Profile reset to defaults")
                        }
                    })
                }
            }
            
            MenuSeparator {}
            
            MenuItem {
                text: qsTr("Open Profiles Folder...")
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        if (controller) controller.openProfilesFolder()
                    })
                }
            }
            
            MenuSeparator {}
            MenuItem { text: qsTr("Configure Axes"); onTriggered: { fileMenu.close(); Qt.callLater(function(){ if (controller) controller.openAxisMapping(); }); } }
            MenuItem { text: qsTr("Joystick Settings..."); onTriggered: { fileMenu.close(); Qt.callLater(function(){ if (controller) controller.openJoystickSettings(); }); } }
            MenuItem { text: qsTr("Button Settings..."); onTriggered: { fileMenu.close(); Qt.callLater(function(){ if (controller) controller.openButtonSettings(); }); } }
            MenuItem { text: qsTr("Rudder Settings..."); onTriggered: { fileMenu.close(); Qt.callLater(function(){ if (controller) controller.openRudderSettings(); }); } }
            MenuSeparator {}
            MenuItem { text: qsTr("Exit"); onTriggered: Qt.quit() }
        }
        Menu {
            id: viewMenu
            title: qsTr("View")
            MenuItem {
                id: debugBordersItem
                text: qsTr("Debug Borders")
                checkable: true
                checked: controller ? controller.debugBorders : false
                onTriggered: { viewMenu.close(); Qt.callLater(function(){ if (controller) controller.debugBorders = checked; }); }
            }
        }
    }

    // Layout loader - switches between Flight Sim and Xbox layouts
    Loader {
        id: layoutLoader
        anchors.fill: parent
        sourceComponent: root.layoutType === "xbox" ? xboxLayout : flightSimLayout
    }

    // Flight Simulator layout component
    Component {
        id: flightSimLayout
        Layouts.FlightSimLayout {
            scaleFactor: root.scaleFactor
        }
    }

    // Xbox Controller layout component
    Component {
        id: xboxLayout
        Layouts.XboxLayout {
            scaleFactor: root.scaleFactor
        }
    }
}
