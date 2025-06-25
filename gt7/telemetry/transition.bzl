def _multiarch_transition_impl(settings, attr):
    return [
        {
            "//command_line_option:platforms": platform,
        }
        for platform in attr.platforms
    ]

multiarch_transition = transition(
    implementation = _multiarch_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

def _multi_arch_impl(ctx):
    return [DefaultInfo(files = depset(ctx.files.image))]

multi_arch = rule(
    implementation = _multi_arch_impl,
    attrs = {
        "image": attr.label(cfg = multiarch_transition),
        "platforms": attr.string_list(mandatory = True),
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
    },
)
