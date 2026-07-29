import cv2
import shutil
import subprocess
import sys
import time


def convert(frame):
    """
    Convert a video frame into true-color Unicode output.
    One terminal character represents two vertical pixels.
    """

    columns, rows = shutil.get_terminal_size()

    width = max(1, columns - 1)
    height = max(2, rows * 2)

    # height must be even because we're processing
    # two rows at a time.
    if height % 2 != 0:
        height += 1

    frame = cv2.resize(frame, (width, height))

    output = []

    for y in range(0, height, 2):

        line = []

        top = frame[y]
        bottom = frame[y + 1]

        for x in range(width):

            b1, g1, r1 = top[x]
            b2, g2, r2 = bottom[x]

            pixel = (
                f"\033[38;2;{r1};{g1};{b1}m"
                f"\033[48;2;{r2};{g2};{b2}m"
                "▀"
            )

            line.append(pixel)

        line.append("\033[0m")
        output.append("".join(line))

    return "\n".join(output)


def main():

    if len(sys.argv) != 2:
        print("\nUsage:")
        print("python termvid.py video.mp4\n")
        return

    filename = sys.argv[1]

    video = cv2.VideoCapture(filename)

    if not video.isOpened():
        print("\nCouldn't open the video.\n")
        return

    fps = video.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 30

    total_frames = int(
        video.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    # ----------------------------------
    # Start the audio player.
    # ----------------------------------

    audio = None

    try:
        audio = subprocess.Popen(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "quiet",
                filename,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except Exception:
        # Continue without audio if ffplay
        # isn't installed.
        audio = None

    # ----------------------------------
    # Prepare the terminal.
    # ----------------------------------

    # clear screen
    print("\033[2J", end="")

    # hide cursor
    print("\033[?25l", end="")

    # move cursor home
    print("\033[H", end="")

    # ----------------------------------
    # MASTER CLOCK
    # ----------------------------------

    master_clock = time.perf_counter()

    try:

        while True:

            # How long has the movie been playing?
            elapsed = (
                time.perf_counter()
                - master_clock
            )

            # Which frame SHOULD we be displaying?
            desired_frame = int(
                elapsed * fps
            )

            # Stop when we've reached the end.
            if desired_frame >= total_frames:
                break

            current_frame = int(
                video.get(
                    cv2.CAP_PROP_POS_FRAMES
                )
            )

            difference = (
                desired_frame
                - current_frame
            )

            # ----------------------------------
            # FRAME SYNCHRONIZATION
            # ----------------------------------

            # If we're significantly behind,
            # jump directly to the desired frame.
            if difference > 3:

                video.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    desired_frame
                )

            # If we're somehow ahead,
            # wait very briefly.
            elif difference < 0:

                time.sleep(0.001)
                continue

            success, frame = video.read()

            if not success:
                break

            text = convert(frame)

            # Move to the top-left corner.
            print("\033[H", end="")

            # Display the frame.
            print(
                text,
                end="",
                flush=True
            )

            # Small sleep so we don't pin
            # an entire CPU core at 100%.
            time.sleep(0.001)

    except KeyboardInterrupt:

        pass

    finally:

        # ----------------------------------
        # CLEAN UP THE AUDIO PROCESS
        # ----------------------------------

        if audio is not None:

            try:
                audio.terminate()
                audio.wait(timeout=1)

            except Exception:

                try:
                    audio.kill()
                except Exception:
                    pass

        # ----------------------------------
        # CLEAN UP OPENCV
        # ----------------------------------

        video.release()

        # ----------------------------------
        # RESTORE THE TERMINAL
        # ----------------------------------

        # reset colors
        print("\033[0m", end="")

        # clear the screen
        print("\033[2J", end="")

        # move cursor home
        print("\033[H", end="")

        # show the cursor again
        print("\033[?25h", end="")

        print("\nThanks for using TermVid!\n")


if __name__ == "__main__":
    main()
