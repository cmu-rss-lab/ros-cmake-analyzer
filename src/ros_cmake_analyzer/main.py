import sys
from argparse import ArgumentParser

from loguru import logger
from ros1 import ROS1CMakeExtractor


def main(arguments: list[str]) -> None:
    parser = ArgumentParser()
    parser.add_argument("ros", type=str, choices=["ros1", "ros2"],
                        help="The ROS major version of the directory")
    parser.add_argument("dir", type=str, help="The directory to get the cmake")
    args = parser.parse_args(arguments)

    if args.ros == "ros1":
        cmake = ROS1CMakeExtractor(args.dir)
    else:
        raise ValueError("ROS2 is not supported yet")

    info = cmake.get_cmake_info()
    for target in info.targets:
        logger.info(f"Target '{target}' has sources: {info.targets[target]}")
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
