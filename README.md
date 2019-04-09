Create Face Recognizer with options to use different AI services or your own AI
========

## Introduction
This project's goal is to enable to test performance of different AI services and let easily connect to new ones.


## Preparing your development environment
Here’s a high-level checklist of what you need to do to setup your development environment.

1. Sign up for an AWS account if you haven't already and create an Administrator User. The steps are published [here](http://docs.aws.amazon.com/lambda/latest/dg/setting-up.html).

2. Ensure that you have Python 2.7+ and Pip on your machine. Instructions for that varies based on your operating system and OS version.

3. Create a Python [virtual environment](https://virtualenv.pypa.io/en/stable/) for the project with Virtualenv. This helps keep project’s python dependencies neatly isolated from your Operating System’s default python installation. **Once you’ve created a virtual python environment, activate it before moving on with the following steps**.

4. Use Pip to install [Open CV](https://github.com/opencv/opencv) 3 python dependencies and then compile, build, and install Open CV 3 (required by Video Cap clients). You can follow [this guide](http://www.pyimagesearch.com/2016/11/28/macos-install-opencv-3-and-python-2-7/) to get Open CV 3 up and running on OS X Sierra with Python 2.7. There's [another guide](http://www.pyimagesearch.com/2016/12/05/macos-install-opencv-3-and-python-3-5/) for Open CV 3 and Python 3.5 on OS X Sierra. Other guides exist as well for Windows and Raspberry Pi

5. Use Pip to install [Pynt](https://github.com/rags/pynt). Pynt enables you to write project build scripts in Python.

6. Clone this GitHub repository. Choose a directory path for your project that does not contain spaces (I'll refer to the full path to this directory as _\<path-to-project-dir\>_).

7. Finally, obtain an IP camera. If you don’t have an IP camera, you can use your smartphone with an IP camera app. This is useful in case you want to test things out before investing in an IP camera. Also, you can simply use your laptop’s built-in camera or a connected USB camera. If you use an IP camera, make sure your camera is connected to the same Local Area Network as the Video Capture client.

## Configurations

In the config folder there are configurations. You can change the values to your own needs. The ones you can change are named as 'SET-THIS'.

## Build commands

This section describes important build commands and how to use them. If you want to use these commands right away to build the prototype, you may skip to the section titled _"Deploy and run the prototype"_.

## Deploy and run the prototype
In this section, we are going use project's build commands to deploy and run the prototype in your AWS account. We’ll use the commands to create the prototype's AWS CloudFormation stack, build and serve the Web UI, and run the Video Cap client.

* Prepare your development environment, and ensure configuration parameters are set as you wish.

* On your machine, in a command line terminal change into the root directory of the project. Activate your virtual Python environment. Then, enter the following commands:

* Now turn on your IP camera or launch the app on your smartphone. Ensure that your camera is accepting connections for streaming MJPEG video over HTTP, and identify the local URL for accessing that stream.

* Then, in a terminal window at the root directory of the project, issue this command:

```bash
$ pynt videocaptureip["<your-ip-cam-mjpeg-url>",<capture-rate>]
```
* Or, if you don’t have an IP camera and would like to use a built-in camera:

```bash
$ pynt videocapture[<frame-capture-rate>]
```

* Few seconds after you execute this step, the dashed area in the Web UI will auto-populate with captured frames, side by side with labels recognized in them.

## When you are done
After you are done experimenting with the prototype, perform the following steps to avoid unwanted costs.

# FAQ

> **Q: Future Question Text?**

> **A:** Answer to the Future Question Text
