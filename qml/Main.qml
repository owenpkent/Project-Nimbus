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
    minimumWidth: 700
    minimumHeight: 450
    title: "Project Nimbus - QML UI"
    background: Rectangle { color: "black" }

    // Scale factor bound to Python bridge; default 1.0
    property real scaleFactor: controller ? controller.scaleFactor : 1.0
    
    // Current profile and layout type
    property string currentProfile: controller ? controller.getCurrentProfile() : "flight_simulator"
    property string layoutType: controller ? controller.getLayoutType() : "flight_sim"
    
    // Track available profiles for dynamic updates
    property var availableProfiles: controller ? controller.getAvailableProfiles() : []
    
    // Initialize window reference for game focus mode
    Component.onCompleted: {
        if (controller) {
            controller.setWindow(root)
        }
    }
    
    // Global mouse tracker for game focus mode
    // This detects when user starts/stops interacting with the window
    MouseArea {
        id: globalMouseTracker
        anchors.fill: parent
        z: -1  // Behind everything so it doesn't block other mouse areas
        propagateComposedEvents: true
        acceptedButtons: Qt.AllButtons
        
        onPressed: function(mouse) {
            if (controller) controller.onMousePressed()
            mouse.accepted = false  // Let event propagate to children
        }
        
        onReleased: function(mouse) {
            if (controller) controller.onMouseReleased()
            mouse.accepted = false
        }
    }
    
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
        function onNoFocusModeChanged(enabled) {
            // Update menu checkbox when mode changes
            noFocusModeItem.checked = enabled
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
            MenuItem { text: qsTr("Exit"); onTriggered: Qt.quit() }
        }
        
        // Settings menu - top level between File and View
        Menu {
            id: settingsMenu
            title: qsTr("Settings")
            
            MenuItem { 
                text: qsTr("Axis Configuration...")
                onTriggered: { 
                    settingsMenu.close()
                    Qt.callLater(function(){ if (controller) controller.openAxisSettings(); })
                } 
            }
            MenuSeparator {}
            MenuItem { 
                text: qsTr("Button Modes...")
                onTriggered: { 
                    settingsMenu.close()
                    Qt.callLater(function(){ if (controller) controller.openButtonSettings(); })
                } 
            }
        }
        
        Menu {
            id: viewMenu
            title: qsTr("View")
            MenuItem {
                id: noFocusModeItem
                text: qsTr("Game Focus Mode")
                checkable: true
                checked: controller ? controller.noFocusMode : false
                enabled: controller ? controller.isNoFocusModeAvailable() : false
                onTriggered: { 
                    viewMenu.close()
                    Qt.callLater(function(){ 
                        if (controller) controller.noFocusMode = checked
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                id: debugBordersItem
                text: qsTr("Debug Borders")
                checkable: true
                checked: controller ? controller.debugBorders : false
                onTriggered: { viewMenu.close(); Qt.callLater(function(){ if (controller) controller.debugBorders = checked; }); }
            }
        }
        
        Menu {
            id: helpMenu
            title: qsTr("Help")
            MenuItem { 
                text: qsTr("GitHub Repository")
                onTriggered: { 
                    helpMenu.close()
                    Qt.openUrlExternally("https://github.com/owenpkent/Project-Nimbus")
                } 
            }
            MenuSeparator {}
            MenuItem { 
                text: qsTr("About Project Nimbus...")
                onTriggered: { 
                    helpMenu.close()
                    Qt.callLater(function(){ aboutDialog.open(); })
                } 
            }
        }
    }
    
    // About Dialog
    Dialog {
        id: aboutDialog
        title: "About Project Nimbus"
        modal: true
        anchors.centerIn: parent
        width: 450
        height: 320
        
        background: Rectangle {
            color: "#2a2a2a"
            border.color: "#555"
            border.width: 1
            radius: 8
        }
        
        header: Label {
            text: aboutDialog.title
            color: "white"
            font.pixelSize: 16
            font.bold: true
            padding: 16
            background: Rectangle { color: "#333"; radius: 8 }
        }
        
        contentItem: Column {
            spacing: 16
            padding: 20
            
            Image {
                source: "qrc:/logo.png"
                width: 80
                height: 80
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                visible: status === Image.Ready
            }
            
            Label {
                text: "Project Nimbus"
                color: "white"
                font.pixelSize: 20
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "Version 2.1"
                color: "#aaa"
                font.pixelSize: 14
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "Virtual controller interface for accessibility and adaptive gaming.\nTransforms mouse input into virtual joystick commands."
                color: "#ccc"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                width: parent.width - 40
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "© 2024-2025 Owen Kent"
                color: "#888"
                font.pixelSize: 11
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "Licensed under MIT License"
                color: "#666"
                font.pixelSize: 10
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
        
        footer: DialogButtonBox {
            Button {
                text: "OK"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            background: Rectangle { color: "#333" }
        }
    }

    // Layout loader - switches between Flight Sim, Xbox, and Adaptive layouts
    Loader {
        id: layoutLoader
        anchors.fill: parent
        sourceComponent: {
            if (root.layoutType === "adaptive") return adaptiveLayout
            if (root.layoutType === "xbox") return xboxLayout
            return flightSimLayout
        }
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

    // Adaptive Controller layout component (accessibility-focused)
    Component {
        id: adaptiveLayout
        Layouts.AdaptiveLayout {
            scaleFactor: root.scaleFactor
        }
    }
}
